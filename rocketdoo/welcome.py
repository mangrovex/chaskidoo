from pyfiglet import Figlet
from rich.console import Console
from rich.panel import Panel

from rocketdoo import __version__

console = Console()


def show_welcome():
    # We generated the logo with pyfiglet.
    fig = Figlet(font="slant")
    logo = fig.renderText("chaskidoo")

    # Chaskidoo palette: piedra (C), terracota and ocre (the knots).
    console.print(f"[bold #F4E9D8]{logo}[/bold #F4E9D8]", end="")
    console.print("[#F4E9D8]  ▪[/#F4E9D8] [#D2603F]●[/#D2603F] [bold #E8A33D]⬤[/bold #E8A33D]   [dim]dev → stage → prod · Manexware[/dim]\n")

    console.print("=" * 60, style="yellow")
    console.print(
        Panel.fit(
            f"""Welcome to the Odoo Development Framework!

This wizard will guide you through the creation of a dockerized Odoo development environment.
Please answer the following questions to customize your project.
If you don't need to modify the values, just press ENTER.

After finishing the guide, you will be able to run your project
with the command: [bold cyan]chk up[/bold cyan]  (or rkd up).

If you have any questions, please check the documentation
or contact the administrator.

Version: [bold green]{__version__}[/bold green]
Based on Rocketdoo by HDMSoft · LGPL-3.0
            """,
            title="[bold #E8A33D]Chaskidoo Init Wizard[/bold #E8A33D]",
            border_style="bright_magenta",
        )
    )

    console.print("\n[bold cyan]Press ENTER to start or CTRL+C to cancel...[/bold cyan]")
    try:
        input()  # Simplemente ignoramos lo que escriba
    except KeyboardInterrupt:
        console.print("\n\n[bold red]Operation cancelled by user.[/bold red]")
        exit(0)
