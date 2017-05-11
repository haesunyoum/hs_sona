import curses
import platform

from log_lib import LOG
from flow_trace import TRACE
from system_info import SYS
from config import CONFIG
from cli import CLI

from asciimatics.widgets import Frame, ListBox, Layout, Divider, Text, \
    Button, Widget, TextBox, PopUpDialog
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import NextScene, StopApplication
from asciimatics.event import KeyboardEvent
from collections import defaultdict

WHITE = '\033[1;97m'
BLUE = '\033[1;94m'
YELLOW = '\033[1;93m'
GREEN = '\033[1;92m'
RED = '\033[1;91m'
BLACK = '\033[1;90m'
BG_WHITE = '\033[0;97m'
BG_BLUEW = '\033[0;37;44m'
BG_SKYW = '\033[0;37;46m'
BG_PINKW = '\033[0;37;45m'
BG_YELLOWW = '\033[0;30;43m'
BG_GREENW = '\033[0;37;42m'
BG_RED = '\033[0;91m'
BG_BLACK = '\033[0;90m'
ENDC = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'

MAIN_WIDTH = 50

class SCREEN():
    main_scr = None

    menu_flag = False
    cli_flag = False
    quit_flag = False
    restart_flag = False
    resize_err_flag = False
    evt_flag = False

    main_instance = None

    @classmethod
    def set_screen(cls):
        cls.main_scr = curses.initscr()

        curses.noecho()
        curses.cbreak()
        curses.start_color()
        cls.main_scr.keypad(1)
        curses.curs_set(0)
        cls.main_scr.refresh()

        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_MAGENTA, curses.COLOR_BLACK)

    @classmethod
    def set_main_str(cls, x, y, str, color):
        try:
            cls.main_scr.addstr(x, y, str, color)
            cls.refresh_screen()
        except:
            LOG.exception_err_write()

    @classmethod
    def screen_exit(cls):
        try:
            curses.endwin()
        except:
            LOG.exception_err_write()

    @classmethod
    def refresh_screen(cls):
        try:
            cls.main_scr.refresh()
        except:
            LOG.exception_err_write()

    @classmethod
    def get_screen(cls):
        return cls.main_scr

    @classmethod
    def get_ch(cls):
        try:
            return cls.main_scr.getch()
        except:
            LOG.exception_err_write()
            return ''

    @classmethod
    def draw_system(cls, menu_list):
        try:
            box_system = cls.display_sys_info()

            cls.draw_refresh_time(menu_list)

            box_system.refresh()
        except:
            LOG.exception_err_write()

    @classmethod
    def draw_refresh_time(cls, menu_list):
        try:
            time_color = curses.color_pair(3)

            str_time = 'Last Check Time [' + SYS.last_check_time.split('.')[0] + ']'
            cls.set_main_str(SYS.get_sys_line_count() + 2 + 3 + len(menu_list) + 2 + 1, MAIN_WIDTH - len(str_time), str_time, time_color)
        except:
            LOG.exception_err_write()
            
    @classmethod
    def draw_trace_warning(cls):
        try:
            warn_color = curses.color_pair(3)

            str = 'Flow traces can not be executed on screens smaller than 100 * 25.'
            cls.set_main_str(3, 3, str, warn_color)

            str = 'After 3 seconds, it automatically switches to the main screen.'
            cls.set_main_str(4, 3, str, warn_color)

            import time
            str = '>>> 3 seconds remaining >>>'
            cls.set_main_str(6, 10, str, warn_color)
            time.sleep(1)

            str = '>>> 2 seconds remaining >>>'
            cls.set_main_str(6, 10, str, warn_color)
            time.sleep(1)

            str = '>>> 1 second remaining >>> '
            cls.set_main_str(6, 10, str, warn_color)
            time.sleep(1)
        except:
            LOG.exception_err_write()

    @classmethod
    def draw_menu(cls, menu_list, selected_menu_no):
        try:
            box_menu = cls.draw_select(menu_list, selected_menu_no)
            box_menu.refresh()
        except:
            LOG.exception_err_write()

    @staticmethod
    def draw_select(menu_list, selected_menu_no):
        box_type = curses.newwin(len(menu_list) + 2, MAIN_WIDTH, SYS.get_sys_line_count() + 3 + 3, 1)
        box_type.box()

        try:
            highlightText = curses.color_pair(1)
            normalText = curses.A_NORMAL

            box_type.addstr(0, 22, ' MENU ', normalText)

            for i in range(1, len(menu_list) + 1):
                if i is selected_menu_no:
                    box_type.addstr(i, 2, str(i) + "." + menu_list[i - 1], highlightText)
                else:
                    box_type.addstr(i, 2, str(i) + "." + menu_list[i - 1], normalText)
        except:
            LOG.exception_err_write()

        return box_type

    @classmethod
    def draw_event(cls):
        try:
            warn_color = curses.color_pair(3)

            box_event = curses.newwin(3, MAIN_WIDTH, SYS.get_sys_line_count() + 3, 1)
            box_event.box()

            normalText = curses.A_NORMAL

            box_event.addstr(0, 22, ' EVENT ', normalText)

            # if occur event
            if cls.evt_flag:
                str = '[Event occurred]'

                box_event.addstr(1, 2, str, warn_color)
                box_event.addstr(1, 2 + len(str), ' Check the event history.', normalText)
            else:
                str = 'none'

                box_event.addstr(1, 2, str, normalText)

            box_event.refresh()
        except:
            LOG.exception_err_write()

    @classmethod
    def display_header(cls, menu):
        try:
            width = 60
            print BG_WHITE + "|%s|" % ('-' * width).ljust(width) + ENDC
            print BG_WHITE + '|' + BG_BLUEW + BOLD + \
                    ("{0:^" + str(width) + "}").format(menu) + BG_WHITE + '|' + ENDC
            print BG_WHITE + "|%s|" % ('-' * width).ljust(width) + ENDC
        except:
            LOG.exception_err_write()

    @classmethod
    def display_sys(cls, header = False):
        try:
            width = 60

            if not header:
                print BG_WHITE + "|%s|" % ('-' * width).ljust(width) + ENDC

            print '| SYSTEM INFO | TIME : ' + SYS.last_check_time.split('.')[0] + \
                  ("{0:>" + str(width - len(SYS.last_check_time.split('.')[0]) - len('SYSTEM INFO | TIME : ')) + "}").format('|') + ENDC
            print BG_WHITE + "|%s|" % ('-' * width).ljust(width) + ENDC

            sorted_list = sorted(SYS.sys_list.keys())

            for sys in sorted_list:
                status = 'NOK'
                if (dict)(SYS.sys_list[sys])['IP'] == 'ok' and (dict)(SYS.sys_list[sys])['APP'] == 'ok':
                    status = 'OK'

                color = GREEN
                if status is not 'OK':
                    color = RED
                print '| ' + sys.ljust(6) + ' [' + color + status + BG_WHITE + ']' + \
                      ("{0:>" + str(width - 6 - len(status) - 3) + "}").format('|') + ENDC

            print BG_WHITE + "|%s|" % ('-' * width).ljust(width) + ENDC
        except:
            LOG.exception_err_write()

    @classmethod
    def display_help(cls):
        try:
            print ''
            for cmd in CLI.command_list:
                print '\t' + cmd.ljust(15) + '  ' + CONFIG.get_cmd_help(cmd)

                if (CONFIG.get_config_instance().has_section(cmd)):
                    opt_list = CONFIG.cli_get_value(cmd, CONFIG.get_cmd_opt_key_name())

                    print '\t' + ' '.ljust(15) + '  - option : ' + opt_list.strip()
            print ''
        except:
            LOG.exception_err_write()

    @classmethod
    def start_screen(cls, screen, scene):
        if (screen.width < 100 or screen.height < 25):
            cls.resize_err_flag = True
            return

        scenes = [
            Scene([FlowTraceView(screen)], -1, name="Flow Trace")
        ]

        screen.play(scenes, stop_on_resize=True, start_scene=scene)

    @classmethod
    def set_exit(cls):
        cls.quit_flag = True

    @classmethod
    def display_sys_info(cls):
        box_sys = curses.newwin(SYS.get_sys_line_count() + 2, MAIN_WIDTH, 1, 1)
        box_sys.box()

        try:
            status_text_OK = curses.color_pair(2)
            status_text_NOK = curses.color_pair(3)
            normal_text = curses.A_NORMAL

            box_sys.addstr(0, 18, ' CONTROL PLAN ', normal_text)

            i = 1

            sorted_list = sorted(SYS.sys_list.keys())

            for sys in sorted_list:
                str_info = sys.ljust(6) + ' ['
                box_sys.addstr(i, 2, str_info)

                str_status = 'NOK'
                if (dict)(SYS.sys_list[sys])['IP'] == 'ok' and (dict)(SYS.sys_list[sys])['APP'] == 'ok':
                    str_status = 'OK'

                if str_status is 'OK':
                    box_sys.addstr(i, 2 + len(str_info), str_status, status_text_OK)
                else:
                    box_sys.addstr(i, 2 + len(str_info), str_status, status_text_NOK)

                box_sys.addstr(i, 2 + len(str_info) + len(str_status), ']')
                i += 1

                # add app status
        except:
            LOG.exception_err_write()

        return box_sys

class FlowTraceView(Frame):
    trace_history = []
    real_trace = []

    def __init__(self, screen):
        try:
            super(FlowTraceView, self).__init__(screen,
                                                screen.height,
                                                screen.width,
                                                x = 0, y = 0,
                                                hover_focus=True,
                                                title=" FLOW TRACE ",
                                                reduce_cpu=True)

            self._screen = screen

            layout_cpt = Layout([1])
            self.add_layout(layout_cpt)

            layout_cpt.add_widget(Text(" [COMPUTE] ", "COMPUTE"))
            layout_cpt.add_widget(Divider())

            i = 0
            for key, value in TRACE.trace_l2_cond_list + TRACE.trace_l3_cond_list:
                if i % 2 == 0:
                    layout_line = Layout([1, 35, 3, 35, 1])
                    self.add_layout(layout_line)

                    layout_line.add_widget(Text(self.key_name(key), value), 1)
                else:
                    layout_line.add_widget(Text(self.key_name(key), value), 3)

                i = i + 1

            layout_btn = Layout([1, 3, 3, 3, 3])
            self.add_layout(layout_btn)
            layout_btn.add_widget(Divider(), 0)
            layout_btn.add_widget(Divider(), 1)
            layout_btn.add_widget(Divider(), 2)
            layout_btn.add_widget(Divider(), 3)
            layout_btn.add_widget(Divider(), 4)
            layout_btn.add_widget(Button("Start Trace", self._ok), 1)
            layout_btn.add_widget(Button("Clear All", self.reset), 2)
            layout_btn.add_widget(Button("Menu", self._menu), 3)
            layout_btn.add_widget(Button("Quit", self._quit), 4)
            layout_btn.add_widget(Divider(height=2), 0)
            layout_btn.add_widget(Divider(), 1)
            layout_btn.add_widget(Divider(), 2)
            layout_btn.add_widget(Divider(), 3)
            layout_btn.add_widget(Divider(), 4)

            layout_result = Layout([1], fill_frame=True)
            self.add_layout(layout_result)
            self._trace_result = TextBox(Widget.FILL_FRAME, name='Flow', label='[Flow]', as_string=True)
            layout_result.add_widget(self._trace_result)
            layout_result.add_widget(Divider())

            self._list_view = ListBox(
                5,
                self.trace_history,
                name="LIST_HISTORY",
                label="[HISTORY]")
            layout_history = Layout([1])
            self.add_layout(layout_history)
            layout_history.add_widget(self._list_view)

            self.fix()

            self.palette = defaultdict(
                lambda: (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_CYAN))

            self.palette["selected_focus_field"] = (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_YELLOW)
            self.palette["title"] = (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_CYAN)
            self.palette["edit_text"] = (Screen.COLOUR_BLUE, Screen.A_BOLD, Screen.COLOUR_CYAN)
            self.palette["focus_edit_text"] = (Screen.COLOUR_BLUE, Screen.A_BOLD, Screen.COLOUR_YELLOW)
            self.palette["focus_button"] = (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_YELLOW)
            self.palette["label"] = (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_CYAN)

        except:
            LOG.exception_err_write()

    isKeypad = False
    def process_event(self, event):
        if isinstance(event, KeyboardEvent):
            c = event.key_code

            # mac OS
            if platform.system() == 'Darwin':
                if c == 127:
                    event.key_code = Screen.KEY_BACK
            else:
                if c == 8:
                    event.key_code = Screen.KEY_BACK
                # for keypad
                elif c == -1:
                    return
                elif c == 79:
                    self.isKeypad = True
                    return
                elif (self.isKeypad and c >= 112 and c <= 121):
                    event.key_code = c - 64
                    self.isKeypad = False
                elif c == -102:
                    event.key_code = 46

            # press enter at trace history
            if self._list_view._has_focus and c == 10:
                self.save()
                self.start_trace((self.trace_history[len(self.trace_history) - self._list_view.value])[0], self.real_trace[self._list_view.value - 1])

        return super(FlowTraceView, self).process_event(event)

    def key_name(self, key):
        try:
            default_width = 12

            key = '* ' + key

            if len(key) < default_width:
                for i in range(default_width - len(key)):
                    key = key + ' '

            key = key + ' '
        except:
            LOG.exception_err_write()

        return key

    def reset(self):
        super(FlowTraceView, self).reset()

    def _ok(self):
        self.save()

        saved_data = ''
        real_data = ''
        for key, real_key in TRACE.trace_l2_cond_list + TRACE.trace_l3_cond_list:
            val = self.data[real_key].strip()

            if val != '':
                saved_data = saved_data + key + '=' + val + ','
                real_data = real_data + real_key + '=' + val + ','

        saved_data = saved_data[0:-1]
        real_data = real_data[0:-1]

        self.start_trace(saved_data, real_data)

    def start_trace(self, saved_data, real_data):

        if (len(self.data['COMPUTE'].strip()) == 0):
            self._scene.add_effect(PopUpDialog(self._screen, "Please enter a compute node name.", ["OK"]))
            return

        if not (TRACE.compute_list.has_key(self.data['COMPUTE'].strip())):
            self._scene.add_effect(PopUpDialog(self._screen, 'No ' + self.data["COMPUTE"].strip() + '(COMPUTE NODE) registered', ["OK"]))
            return

        if len(saved_data) == 0:
            self._scene.add_effect(PopUpDialog(self._screen, "Please enter a flow-trace condition.", ["OK"]))
            return

        num = len(self.trace_history) + 1
        data = (saved_data, num)

        self.trace_history.insert(0, data)
        self.real_trace.append(real_data)

        self._list_view.value = len(self.trace_history)

        cmd_rt = TRACE.ssh_exec(TRACE.compute_id, TRACE.compute_list[self.data['COMPUTE'].strip()], real_data)

        self._trace_result.value = cmd_rt

    @staticmethod
    def _menu():
        SCREEN.menu_flag = True
        raise StopApplication("User terminated app")

    @staticmethod
    def _quit():
        SCREEN.set_exit()
        raise StopApplication("User pressed quit")
