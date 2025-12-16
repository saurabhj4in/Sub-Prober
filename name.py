import pyfiglet
from termcolor import colored

ascii_banner = pyfiglet.figlet_format("Subdomain Prober")
print(colored(ascii_banner, "cyan"))
print(colored("v1.0.0", "green"))
print(colored("yourtool.io", "yellow"))
