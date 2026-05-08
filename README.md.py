import customtkinter as ctk
from scapy.all import ARP, Ether, srp, sniff, IP, DNS, DNSQR
import threading
import socket

class NetworkMaster(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Network Monitor Pro | مراقب الشبكة الذكي")
        self.geometry("900x600")
        ctk.set_appearance_mode("dark")

        # تقسيم الشاشة (يسار: أزرار، يمين: عرض)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # القائمة الجانبية
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=10)
        self.sidebar.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.label = ctk.CTkLabel(self.sidebar, text="التحكم", font=("Arial", 18, "bold"))
        self.label.pack(pady=20)

        self.btn_scan = ctk.CTkButton(self.sidebar, text="فحص الأجهزة", command=self.start_scan_thread)
        self.btn_scan.pack(pady=10, padx=10)

        self.btn_sniff = ctk.CTkButton(self.sidebar, text="مراقبة المواقع", command=self.start_sniffing_thread)
        self.btn_sniff.pack(pady=10, padx=10)

        # منطقة العرض مع التنسيق
        self.display_area = ctk.CTkTextbox(self, font=("Consolas", 13))
        self.display_area.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.display_area.insert("0.0", "--- جاهز للعمل. اختر 'فحص الأجهزة' لرؤية المتصلين ---\n")

    def get_my_ip(self):
        return socket.gethostbyname(socket.gethostname())

    # --- وظيفة فحص الأجهزة ---
    def start_scan_thread(self):
        threading.Thread(target=self.scan_network, daemon=True).start()

    def scan_network(self):
        self.display_area.delete("0.0", "end")
        self.display_area.insert("end", "[+] جاري فحص الشبكة... قد يستغرق الأمر ثواني\n")
        
        try:
            my_ip = self.get_my_ip()
            ip_range = ".".join(my_ip.split('.')[:-1]) + ".1/24"
            
            # إرسال طلب ARP لكل الأجهزة
            ans, _ = srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=ip_range), timeout=2, verbose=False)
            
            self.display_area.insert("end", f"{'IP Address':<20} | {'MAC Address':<20}\n")
            self.display_area.insert("end", "-"*50 + "\n")
            
            for sent, rcv in ans:
                self.display_area.insert("end", f"{rcv.psrc:<20} | {rcv.hwsrc:<20}\n")
        except Exception as e:
            self.display_area.insert("end", f"خطأ: تأكد من تشغيل البرنامج كمسؤول (Admin)\n{e}")

    # --- وظيفة مراقبة المواقع ---
    def start_sniffing_thread(self):
        self.display_area.delete("0.0", "end")
        self.display_area.insert("end", "[!] جاري مراقبة طلبات DNS (المواقع)... اضغط 'فحص الأجهزة' للإيقاف\n\n")
        threading.Thread(target=self.sniff_packets, daemon=True).start()

    def process_packet(self, pkt):
        # البحث عن طلبات DNS (المواقع التي يتم زيارتها)
        if pkt.haslayer(DNSQR):
            site = pkt[DNSQR].qname.decode('utf-8')
            ip_src = pkt[IP].src
            self.display_area.insert("end", f"[زيارة موقع] الجهاز {ip_src} دخل على: {site}\n")
            self.display_area.see("end") # النزول التلقائي لآخر سطر

    def sniff_packets(self):
        try:
            # فلترة حزم DNS فقط (التي تحتوي على أسماء المواقع)
            sniff(filter="udp port 53", prn=self.process_packet, store=0)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    app = NetworkMaster()
    app.mainloop()
