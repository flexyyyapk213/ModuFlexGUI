# ModuFlexGUI
# Copyright (C) 2026 flexyyyapk213

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from flet_android_notifications import FletAndroidNotifications
import flet as ft
import json
from pathlib import Path
import asyncio
import os
import sys
import random

class SafeView(ft.View):
    def __init__(self, route: str, controls: list[ft.Control], **kwargs):
        content = ft.Column(controls, expand=True) if len(controls) > 1 else controls[0]
        
        super().__init__(
            route=route,
            controls=[
                ft.SafeArea(
                    content=content,
                    expand=True
                )
            ],
            **kwargs
        )

class ModuFlexGUI:
    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self.page.title = "ModuFlexGUI"
        self.page.theme_mode = ft.ThemeMode.DARK

        self.page.on_view_pop = self.view_pop
        self.page.on_route_change = self.route_change

        self.api_id = ft.TextField(label='API ID', keyboard_type=ft.KeyboardType.NUMBER)
        self.api_hash = ft.TextField(label='API Hash')
        self.phone_number = ft.TextField(label='Номер телефона', keyboard_type=ft.KeyboardType.PHONE)
        self.password = ft.TextField(label='Пароль', password=True)
        self.wakelock = None

        self.main_menu = ft.Column(controls=[
            ft.Text('ModuFlex установлен.'),
            ft.Row(controls=[ft.Button('Запустить ModuFlex', on_click=self.start_moduflex)], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row(controls=[
                ft.Button('A', bgcolor="white", color="black", on_click=lambda e: asyncio.create_task(self.write_to_stdin('A'))), ft.Button('Y', bgcolor="green", color="black", on_click=lambda e: asyncio.create_task(self.write_to_stdin('Y'))), ft.Button('N', bgcolor="red", color="black", on_click=lambda e: asyncio.create_task(self.write_to_stdin('N')))
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(content=ft.ListView(auto_scroll=True, spacing=2, padding=5), bgcolor="#252a30", align=ft.Alignment.CENTER, width=600, height=300),
            ft.Row(controls=[ft.TextField(label='stdin', border_radius=ft.BorderRadius.only(top_left=15, bottom_left=15), border_color='#666666'), ft.Button('send', bgcolor='#5d97f5', style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=ft.BorderRadius.only(top_right=15, bottom_right=15)), padding=ft.Padding(top=21.8, bottom=21.8)), on_click=self.wrs_field)], alignment=ft.MainAxisAlignment.CENTER, spacing=0)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        self.inst_moduflex = ft.Column(controls=[
            ft.Button('Установить ModuFlex', on_click=self.install_moduflex),
            ft.Container(content=ft.ListView(auto_scroll=True, spacing=2, padding=5), bgcolor="#252a30", align=ft.Alignment.CENTER, width=600, height=300)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        self.main_menu.controls[3].content.controls.append(ft.Text('Добро пожаловать в ModuFlex!', font_family="Consolas", size=13, color="#00ff00"))
        self.inst_moduflex.controls[1].content.controls.append(ft.Text('Нажмите на кнопку "Установить ModuFlex" для установки ModuFlex на ваше устройство.', font_family="Consolas", size=13, color="#00ff00"))

        self.terminal_moduflex = None
        self.notification = FletAndroidNotifications()

        self.rooms = {
            "/": self.main_room,
            "/registration": self.registration_room
        }

        # All this is not transmitted anywhere and is not stored anywhere except here.
        self.user_data = {
            "api_id": None,
            "api_hash": None,
            "phone_number": None,
            "password": None
        }

        self.route_change('/')
    
    def view_pop(self, e):
        self.page.views.pop()
        
        top_view = self.page.views[-1]
        self.route_change(top_view.route)
    
    def main_room(self) -> ft.View:
        try:
            # File for storing account data
            with open('moduflex_datasession.json') as f:
                self.user_data = json.load(f)
        except FileNotFoundError:
            with open('moduflex_datasession.json', 'w') as f:
                json.dump(self.user_data, f)
        
        if self.user_data['phone_number'] is not None:
            room = self.main_menu
            if not Path(os.getcwd()).joinpath('ModuFlex').exists():
                room = self.inst_moduflex
            return SafeView(route='/', controls=[
                ft.AppBar(title='Главное меню', center_title=True),
                ft.Container(room, align=ft.Alignment.CENTER)
            ])
        else:
            return self.registration_room()
    
    def registration_room(self) -> ft.View:
        return SafeView(route='/registration', controls=[
            ft.AppBar(title='Вход в аккаунт', center_title=True),
            ft.Container(ft.Column(controls=[
                self.api_id,
                self.api_hash,
                self.phone_number,
                self.password,
                ft.Button('Подтвердить', on_click=self.check_data)
            ]), align=ft.Alignment.CENTER)
        ])
    
    def check_data(self, e: ft.ControlEvent):
        if '' in [self.api_id.value, self.api_hash.value, self.phone_number.value]:
            self.alert('Введите данные от аккаунта.')
            return
        
        self.user_data['api_id'] = self.api_id.value
        self.user_data['api_hash'] = self.api_hash.value
        self.user_data['phone_number'] = self.phone_number.value.replace('+', '')
        self.user_data['password'] = self.password.value

        self.save_user_data()
        
        self.route_change('/')
    
    def alert(self, message: str):
        self.page.show_dialog(
            ft.SnackBar(
                content=ft.Container(
                    content=ft.Text(
                        message,
                        color=ft.Colors.BLACK,
                        size=14,
                        weight=ft.FontWeight.W_500,
                        text_align=ft.TextAlign.CENTER,
                        max_lines=None, 
                    ),
                    padding=ft.Padding.symmetric(vertical=8, horizontal=12), 
                ),
                behavior=ft.SnackBarBehavior.FLOATING,
                bgcolor="#E6FFFFFF",
                elevation=4,
                duration=3000,
                padding=0,
                margin=ft.Margin.only(bottom=40, left=20, right=20), 
                shape=ft.RoundedRectangleBorder(radius=20)
            )
        )
    
    def route_change(self, route: str):
        self.page.views.clear()
        
        if self.rooms.get(route) is None:
            self.page.views.append(self.unknown_route(route))
            self.page.update()
            return
        
        self.page.views.append(self.rooms[route]())
        self.page.update()
    
    def unknown_route(self, route: str):
        return ft.View(route=route, controls=[ft.Text(value='Unknown route. Please, go to the main page.')])
    
    def save_user_data(self):
        with open('moduflex_datasession.json', 'w') as f:
            json.dump(self.user_data, f)
    
    async def install_moduflex(self, e: ft.ControlEvent):
        self.inst_moduflex.controls[0].disabled = True
        self.page.update()

        self.inst_moduflex.controls[1].content.controls.append(ft.Text('Начало установки ModuFlex...', font_family="Consolas", size=13, color="#00ff00"))
        await asyncio.sleep(0.1)

        install_git = await asyncio.create_subprocess_exec('choco', 'install', 'git', '-y', stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)

        await self.read_and_display_cons(install_git, self.inst_moduflex.controls[1].content.controls)
        
        await install_git.wait()
        
        if install_git.returncode != 0:
            self.alert('Ошибка при установке git.')
        
        self.inst_moduflex.controls[1].content.controls.append(ft.Text('Git успешно установлен.', font_family="Consolas", size=13, color="#00ff00"))
        await asyncio.sleep(0.1)

        self.inst_moduflex.controls[1].content.controls.append(ft.Text('Клонирование ModuFlex...', font_family="Consolas", size=13, color="#00ff00"))
        await asyncio.sleep(0.1)
        
        clone_moduflex = await asyncio.create_subprocess_exec('git', 'clone', 'https://github.com/flexyyyapk213/ModuFlex.git', '-b', 'main', stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)

        await self.read_and_display_cons(clone_moduflex, self.inst_moduflex.controls[1].content.controls)
        
        await clone_moduflex.wait()
        
        if clone_moduflex.returncode != 0:
            self.alert('Ошибка при клонировании ModuFlex.')
        
        with open('ModuFlex/config.ini', 'w') as f:
            data = [
                f'api_id = {self.user_data["api_id"]}\n',
                f'api_hash = "{self.user_data["api_hash"]}"\n',
                f'phone_number = {self.user_data["phone_number"]}\n',
                'send_message = true\n',
                'one_download_libs = true\n',
                'use_botvenv = true\n'
            ]

            if self.user_data['password'] not in ['', None]:
                data.append(f'password = "{self.user_data["password"]}"')

            f.writelines(data)
        
        self.inst_moduflex.controls[1].content.controls.append(ft.Text('ModuFlex успешно склонирован.', font_family="Consolas", size=13, color="#377ded"))
        await asyncio.sleep(0.1)

        self.route_change('/')
    
    async def start_moduflex(self, e: ft.ControlEvent):
        if not await self.notification.request_permissions():
            return

        self.page.run_task(self.work_moduflex)

    async def work_moduflex(self):
        self.main_menu.controls[1].controls[0].disabled = True
        self.main_menu.controls[1].controls.append(ft.Button('Stop', bgcolor="red", on_click=self.finish_moduflex))
        self.page.update()

        # self.wakelock = ft.Wakelock()
        # self.page.overlay.append(self.wakelock)
        # self.page.update()

        # await self.wakelock.enable()

        try:
            await self.notification.start_foreground_service(
                1,
                '🟢Старт ModuFlex',
                'Вы запустили ModuFlex' + random.choice(['😎', '🎉', '⭐', '❤', '✨']),
                foreground_service_types=['special_use'],
                ongoing=True,
                start_type='start_sticky'
            )

            self.terminal_moduflex = await asyncio.create_subprocess_exec('python', os.path.abspath('ModuFlex/run.py'), stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)

            while self.terminal_moduflex.returncode is None:
                if self.terminal_moduflex.stdout:
                    buffer = ''
                    while True:
                        try:
                            chunk = await asyncio.wait_for(
                                self.terminal_moduflex.stdout.read(1024), 
                                timeout=0.5
                            )
                        except asyncio.TimeoutError:
                            if self.terminal_moduflex.returncode is not None:
                                self.main_menu.controls[3].content.controls.append(ft.Text(buffer, font_family="Consolas", size=13, color="#00ff00"))
                                break
                            continue

                        if not chunk:
                            self.main_menu.controls[3].content.controls.append(ft.Text(buffer, font_family="Consolas", size=13, color="#00ff00"))
                            break
                        
                        buffer += chunk.decode('utf-8', errors='ignore')

                        lines = buffer.split('\n')

                        buffer = lines.pop()

                        for line in lines:
                            self.main_menu.controls[3].content.controls.append(ft.Text(line, font_family="Consolas", size=13, color="#00ff00"))

                        self.page.update()
                
                await asyncio.sleep(1)
        except Exception as _e:
            self.alert(str(_e))
        finally:
            await self.terminal_moduflex.wait()

            self.terminal_moduflex = None
            
            # try:
            #     await self.wakelock.disable()
            # except:
            #     pass
        
            self.main_menu.controls[1].controls[0].disabled = False
            self.main_menu.controls[1].controls.pop(1)
            self.main_menu.controls[3].content.controls.clear()
            self.page.update()
    
    async def finish_moduflex(self, e: ft.ControlEvent):
        print('kill')
        try:
            self.terminal_moduflex.terminate()

            await self.terminal_moduflex.wait()
        except ProcessLookupError:
            pass
        except Exception as _e:
            self.alert(str(_e))
    
    async def write_to_stdin(self, text: str):
        if self.terminal_moduflex is None:
            return

        text = text + '\n'

        self.terminal_moduflex.stdin.write(text.encode('utf-8'))
        await self.terminal_moduflex.stdin.drain()
    
    async def read_and_display_cons(self, proc: asyncio.subprocess.Process, list_v: ft.ListView):
        buffer = ''
        listv_bf: ft.Text = None
        while True:
            try:
                chunk = await asyncio.wait_for(
                    proc.stdout.read(1024), 
                    timeout=0.5
                )
            except asyncio.TimeoutError:
                if proc.returncode is not None:
                    if buffer: list_v.append(ft.Text(buffer, font_family="Consolas", size=13, color="#00ff00"))
                    break
                continue
            if not chunk:
                if buffer: list_v.append(ft.Text(buffer, font_family="Consolas", size=13, color="#00ff00"))
                break

            buffer += chunk.decode('utf-8', errors='ignore')

            lines = buffer.split('\n')

            buffer = lines.pop()

            for line in lines:
                if listv_bf is not None:
                    listv_bf.value += line + '\n'
                    listv_bf = None
                list_v.append(ft.Text(line, font_family="Consolas", size=13, color="#00ff00"))
            else:
                if buffer:
                    listv_bf = ft.Text(buffer)
                    list_v.append(listv_bf)
            
            self.page.update()
    
    async def wrs_field(self, e):
        if self.main_menu.controls[4].controls[0].value != '': await self.write_to_stdin(self.main_menu.controls[4].controls[0].value)
        else:
            self.alert('Введите текст!')
        
        self.main_menu.controls[4].controls[0].value = ''
        self.page.update()
    
    async def window_event(self, e):
        print(e.data)
        if e.data == "close":
            if self.terminal_moduflex is not None:
                self.terminal_moduflex.terminate()
                await self.wakelock.disable()
                await self.page.window.destroy()
                sys.exit(0)

if __name__ == "__main__":
    ft.run(ModuFlexGUI, view=ft.AppView.FLET_APP)