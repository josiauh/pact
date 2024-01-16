#!/usr/bin/python3
import configparser
import os
import typer
import requests
import json
import shutil
import tarfile
from rich import print
from rich.panel import Panel
import platform
from typing_extensions import Annotated
os.makedirs("/pactPack" if not platform.system().lower() == "windows" else "C:\\pactPack", exist_ok=True)
path = os.environ["PATH"].split(os.pathsep)
app = typer.Typer()
addGroup = typer.Typer()
dir_path = os.path.dirname(os.path.realpath(__file__))
listGroup = typer.Typer()
app.add_typer(addGroup, name="add")
app.add_typer(listGroup, name="list")
config = configparser.ConfigParser()
config.read("/pactPack/" if not platform.system().lower() == "windows" else "C:\\pactPack\\" + "pactConfig.conf")
if config.sections() == []:
    with open("/pactPack/" if not platform.system().lower() == "windows" else "C:\\pactPack\\" + "pactConfig.conf", "w") as f:
        f.write("[repositories]\ndefault = https://josiauh.com/pactOfficialRepo/")
    config.read("/pactPack/" if not platform.system().lower() == "windows" else "C:\\pactPack\\" + "pactConfig.conf")
if "/pactPack" if not platform.system().lower() == "windows" else "C:\\pactPack" not in path:
    os.system(f"{dir_path}{os.path.sep}{'addPath' if not platform.system().lower() == 'windows' else 'addpath.bat'}")


@addGroup.command()
def package(name: Annotated[str, typer.Argument(help="The package name.")]):
    for rname, url in config.items("repositories") :
        print(f"Looking in repository {rname} ({url})")
        manifest = requests.get(url + "/manifest.json")
        if manifest.status_code == 404:
            print("[red]Manifest not found. [/red]")
            continue
        manifest = json.load(manifest.text)
        for pname, pkg in manifest:
            if pname == name:
                if platform.system().lower() in pkg["platforms"]:
                    package = requests.get(url + f"/{pkg['name']}-{platform.system().lower()}.tar.gz")
                    if package.status_code == 404:
                        print("[red]Package tar.gz not found. Would you like to search the next repo?[/red]")
                        print(Panel(f"You should use the [bold]basename[/bold] of the tar.gz file, and have each platform in it.\n\nSomething like: \"{name}-{platform.system().lower()}.tar.gz\"", title="Repo creators"))
                        if input("y/n: ").lower() in ["yes", "y"]:
                            continue
                        else:
                            break
                    with open(f"{pkg['name']}-{platform.system().lower()}.tar.gz", "w") as f:
                        f.write(package.text)
                    with tarfile.open(f"{pkg['name']}-{platform.system().lower()}.tar.gz") as f:
                        f.extractall("/pactPack/" if not platform.system().lower() == "windows" else "C:\\pactPack\\" + f"{name}")
                    print("[green]Completed![/green] ")
                else:
                    print("[red]Your platform is not supported. Would you like to search the next repo?[/red]")
                    if input("y/n: ").lower() in ["yes", "y"]:
                        continue
                    else:
                        break

@addGroup.command()
def repository(name: Annotated[str, typer.Argument(help="The repository name.")], url: Annotated[str, typer.Argument(help="The repo URL.")]):
    config["repositories"][name] = url
    print(f"Added repository {name}.")

@listGroup.command()
def repos():
    for rname, url in config.items("repositories"):
        print(f"{rname} ({url})")

@listGroup.command()
def packages():
    for dir in os.listdir("/pactPack" if not platform.system().lower() == "windows" else "C:\\pactPack"):
        if os.path.isdir(dir):
            print(dir)

@app.command()
def repoWizard():
    print("Welcome to the repo wizard!")
    print(Panel("The tar.gz format is (name)-(platform).tar.gz.\nThe platform name for macOS should be darwin, not mac or macOS.\nIf you need extra resources, zip those along with it!\nIf these tar files are not found, they are automatically created with your executable.", title=".tar.gz info"))
    platforms = ["linux", "darwin", "windows"]
    template = """{
        "{0}": {
            "name": "{1}",
            "platforms": {2}
        }
    }"""
    winsup = input("Do you want windows support (y/n)? ")
    if winsup.lower() in ["n", "no"]:
        platforms.remove("windows")
    darwinsup = input("Do you want macOS/darwin support? ")
    if darwinsup.lower() in ["n", "no"]:
        platforms.remove("darwin")
    linuxsup = input("Do you want linux support? ")
    if linuxsup.lower() in ["n", "no"]:
        platforms.remove("linux")
    tarname = input("What is the tar.gz name? (MUST BE THE SAME FOR ALL TARS, AND NO EXTENSION!) ")
    for plat in platforms:
        if not os.path.exists(f"{tarname}-{plat}.tar.gz"):
            print("[yellow]Not found.[/yellow]")
            targz = tarfile.TarFile(f"{tarname}-{plat}.tar.gz", 'w')
            with open(input(f"Input your {plat} executable: ")) as f:
                targz.add(f.name)
            print("[green]Zipped!")
        else:
            print(f"[green]{plat} tar.gz file found!")
    manifest = template.format(input("Put the DISCOVERABLE name of your package. "), tarname, str(platforms))
    print(manifest)
    repoName = input("Now one more thing... your repo name! What is it?")
    os.makedirs(repoName)
    with open(repoName + "/manifest.json", "w") as f:
        f.write(manifest)
    for plat in platforms:
        shutil.copy2(f"{tarname}-{plat}.tar.gz", repoName)
    print(Panel("You're finished!\nNow you can host this using github pages, python's http.server module, or anything else!", title=f"{repoName} created!"))
    
        

if __name__ == "__main__":
    app()