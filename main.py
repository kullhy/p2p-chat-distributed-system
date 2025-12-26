from ui.main_gui import P2PChatApp

import sys

if __name__ == "__main__":
    tcp_port = 6000
    if len(sys.argv) >= 2:
        tcp_port = int(sys.argv[1])

    app = P2PChatApp(tcp_port=tcp_port)
    app.mainloop()
