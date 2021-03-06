#!/usr/bin/python
import os
import sys
import time
import threading
import readline
import curses
import multiprocessing

import cli_rest

from log_lib import LOG
from config import CONFIG
from system_info import SYS
from cli import CLI
from flow_trace import TRACE
from log_lib import USER_LOG
from screen import SCREEN

menu_list = ["CLI", "Flow Trace", "Event List"]

def main():
    try:
        from asciimatics.scene import Scene
    except:
        print "This program requires the asciimatics package."
        print 'Please run \'sudo pip install asciimatics\' and try again.'
        return

    # add for readline bug fix
    os.unsetenv('LINES')
    os.unsetenv('COLUMNS')

    # read config
    if not CONFIG.init_config(LOG):
        print 'read config fail...'
        return

    # set log
    LOG.set_default_log('sonawatched_err.log')

    # set cli log
    cli_log = USER_LOG()
    cli_log.set_log('sonawatched_cli.log', CONFIG.get_cli_log_rotate(), int(CONFIG.get_cli_log_backup()))
    CLI.set_cli_log(cli_log)

    # set trace log
    trace_log = USER_LOG()
    trace_log.set_log('sonawatched_trace.log', CONFIG.get_trace_log_rotate(), int(CONFIG.get_trace_log_backup()))
    TRACE.set_trace_log(trace_log)

    # read log option
    LOG.set_log_config()

    # Start RESTful server for event
    evt = multiprocessing.Event()
    disconnect_evt = multiprocessing.Event()

    # create listen event thread
    evt_thread = threading.Thread(target=listen_evt, args=(evt,))
    evt_thread.daemon = False
    evt_thread.start()

    conn_evt_thread = threading.Thread(target=listen_disconnect_evt, args=(disconnect_evt,))
    conn_evt_thread.daemon = False
    conn_evt_thread.start()

    try:
        # create rest server process
        cli_rest.rest_server_start(evt, disconnect_evt)
    except:
        print 'Rest Server failed to start'
        print 'Processing shutdown...'
        LOG.exception_err_write()
        SYS.set_sys_thr_flag(False)
        conn_evt_thread.join()
        evt_thread.join()
        return

    # regi event
    if CLI.send_regi() == False:
        print 'Event registration failed'
        print 'Processing shutdown...'
        LOG.exception_err_write()
        SYS.set_sys_thr_flag(False)
        conn_evt_thread.join()
        evt_thread.join()
        return

    # inquiry controller info
    try:
        res_code, sys_info = CLI.req_sys_info()
    except:
        print "Cannot connect rest server."
        print 'Processing shutdown...'
        CLI.send_regi('unregi')
        SYS.set_sys_thr_flag(False)
        conn_evt_thread.join()
        evt_thread.join()
        return

    if res_code != 200:
        print "Rest server does not respond to the request."
        print "code = " + str(res_code)
        print 'Processing shutdown...'
        CLI.send_regi('unregi')
        SYS.set_sys_thr_flag(False)
        conn_evt_thread.join()
        evt_thread.join()
        return

    SYS.set_sys_info(sys_info)

    # set command list
    CLI.set_cmd_list()

    # set trace cond list
    TRACE.set_cnd_list()

    # set search list
    CLI.set_search_list()

    set_readline_opt()

    # system check
    check_system()

    # select input menu
    select_menu()

    if (SCREEN.menu_flag):
        # restart for redrawing
        python = sys.executable
        os.execl(python, python, *sys.argv)

    # exit
    print 'Processing shutdown...'
    CLI.send_regi('unregi')
    SYS.set_sys_thr_flag(False)
    conn_evt_thread.join()
    evt_thread.join()

    return

def select_menu():
    selected_menu_no = 1

    try:
        SCREEN.set_screen()

        SCREEN.draw_system(menu_list)
        SCREEN.draw_event(SYS.disconnect_flag)
        SCREEN.draw_menu(menu_list, selected_menu_no)

        SYS.set_sys_redraw_flag(True)

        x = SCREEN.get_ch()

        # 27 = ESC
        while x != 27:
            if x == curses.KEY_DOWN:
                if selected_menu_no != len(menu_list):
                    selected_menu_no += 1

            elif x == curses.KEY_UP:
                if selected_menu_no != 1:
                    selected_menu_no -= 1

            elif x == ord("\n"):
                # stop timer
                SYS.set_sys_redraw_flag(False)

                # ?? is it necessary?
                SCREEN.refresh_screen()
                SCREEN.screen_exit()

                menu = menu_list[selected_menu_no - 1]

                if menu == 'CLI' or menu == 'Event List':
                    if menu == 'CLI':
                        SCREEN.display_header(menu_list[selected_menu_no - 1])
                        SCREEN.display_sys(True)
                    elif menu == 'Event List':
                        SCREEN.display_event()

                    readline.set_completer(CLI.pre_complete_cli)

                    while True:
                        # mac OS
                        if 'libedit' in readline.__doc__:
                            CLI.modify_flag = True
                            CLI.save_buffer = readline.get_line_buffer()

                        # select_command (handling tab event)
                        cmd = CLI.input_cmd()
                        cmd = cmd.strip()

                        if CLI.is_menu(cmd):
                            break
                        elif CLI.is_exit(cmd):
                            return
                        elif cmd == 'dis-system':
                            SCREEN.display_sys()
                        elif cmd == 'help':
                            SCREEN.display_help()
                        else:
                            # send command
                            CLI.process_cmd(cmd)

                            while not CLI.get_cli_ret_flag():
                                time.sleep(1)

                elif menu == 'Flow Trace':
                    from asciimatics.screen import Screen
                    from asciimatics.exceptions import ResizeScreenError

                    # clear screen
                    SCREEN.get_screen().clear()
                    SCREEN.screen_exit()

                    last_scene = None

                    while True:
                        try:
                            Screen.wrapper(SCREEN.start_screen, catch_interrupt=True, arguments=[last_scene])

                            if SCREEN.quit_flag:
                                return
                            elif SCREEN.menu_flag:
                                return
                            elif SCREEN.resize_err_flag:
                                SCREEN.draw_trace_warning()
                                SCREEN.screen_exit()
                                SCREEN.menu_flag = True
                                return

                        except ResizeScreenError as e:
                            last_scene = e.scene


            SCREEN.draw_system(menu_list)
            SCREEN.draw_event(SYS.disconnect_flag)
            SCREEN.draw_menu(menu_list, selected_menu_no)
            SCREEN.refresh_screen()

            SYS.set_sys_redraw_flag(True)

            x = SCREEN.get_ch()

        SCREEN.screen_exit()
    except:
        LOG.exception_err_write()

def listen_disconnect_evt(evt):
    while SYS.get_sys_thr_flag():
        evt.wait(3)

        if evt.is_set():
            SYS.disconnect_flag = True
            SCREEN.draw_event(SYS.disconnect_flag)
            evt.clear()

def listen_evt(evt):
    while SYS.get_sys_thr_flag():
        evt.wait(3)

        if evt.is_set():
            evt.clear()
            # system check
            check_system()

def check_system():
    try:
        # inquiry onos info
        res_code, sys_info = CLI.req_sys_info()

        if res_code != 200:
            SYS.disconnect_flag = True
            SCREEN.draw_event(SYS.disconnect_flag)
            LOG.debug_log(
                '[SYSTEM_CHECK_THREAD] Rest server does not respond to the request. RES_CODE = ' + str(res_code))
            return

        ret = SYS.changed_sys_info(sys_info)

        if SYS.get_sys_redraw_flag():
            if ret is True:
                SCREEN.draw_system(menu_list)
                SCREEN.draw_event(SYS.disconnect_flag)
            else:
                SCREEN.draw_refresh_time(menu_list)
    except:
        LOG.exception_err_write()

def set_readline_opt():
    try:
        delims = readline.get_completer_delims().replace("-", "^")
        readline.set_completer_delims(delims)

        # mac OS
        if 'libedit' in readline.__doc__:
            readline.parse_and_bind("bind -e")
            readline.parse_and_bind("bind '\t' rl_complete")
        else:
            readline.parse_and_bind("tab:complete")

        readline.parse_and_bind('set editing-mode vi')
    except:
        LOG.exception_err_write()

def complete_dummy(text, state):
    pass

def call_cli():
    try:
        SCREEN.display_header('CLI')

        readline.set_completer(CLI.pre_complete_cli)

        while True:
            # mac OS
            if 'libedit' in readline.__doc__:
                CLI.modify_flag = True
                CLI.save_buffer = readline.get_line_buffer()

            # select_command (handling tab event)
            cmd = CLI.input_cmd()

            if CLI.is_menu(cmd):
                SCREEN.cli_flag = False
                return
            elif CLI.is_exit(cmd):
                SCREEN.set_exit()
                return
            else:
                # send command
                CLI.process_cmd(cmd)

                while not CLI.get_cli_ret_flag():
                    time.sleep(1)
    except:
        LOG.exception_err_write()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        LOG.exception_err_write()