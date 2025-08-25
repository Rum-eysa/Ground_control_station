# Ssh Commands
# automation/ssh_commands.py - SSH komut şablonları
# =============================================================================

class SSHCommands:
    """SSH komut şablonları"""
    
    @staticmethod
    def get_system_info():
        """Sistem bilgisi komutları"""
        return {
            'hostname': 'hostname',
            'os_info': 'cat /etc/os-release | grep PRETTY_NAME | cut -d"=" -f2 | tr -d \'"\'',
            'kernel': 'uname -r',
            'cpu_model': 'cat /proc/cpuinfo | grep "model name" | head -1 | cut -d":" -f2 | xargs',
            'cpu_cores': 'nproc',
            'memory_total': 'free -m | grep "Mem:" | awk \'{print $2}\'',
            'memory_usage': 'free | grep Mem | awk \'{printf("%.2f", ($3/$2) * 100.0)}\'',
            'disk_usage': 'df -h / | tail -1 | awk \'{print $5}\' | sed \'s/%//\'',
            'temperature': 'cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null | awk \'{print $1/1000}\' || echo "N/A"',
            'uptime': 'uptime -p',
            'load_average': 'uptime | awk -F\'load average:\' \'{print $2}\''
        }
    
    @staticmethod
    def camera_server_commands():
        """Kamera sunucusu komutları"""
        return {
            'check_python': 'which python3',
            'check_opencv': 'python3 -c "import cv2; print(cv2.__version__)" 2>/dev/null || echo "OpenCV not installed"',
            'list_cameras': 'ls /dev/video* 2>/dev/null || echo "No cameras found"',
            'check_camera_permissions': 'ls -la /dev/video0 2>/dev/null || echo "Camera not accessible"',
            'install_opencv': 'sudo apt-get update && sudo apt-get install -y python3-opencv',
            'start_camera_server': 'cd /home/pi && python3 camera_server.py &',
            'stop_camera_server': 'pkill -f camera_server.py',
            'check_server_status': 'pgrep -f camera_server.py || echo "Server not running"',
            'check_port_8888': 'netstat -tulpn | grep :8888 || echo "Port 8888 not listening"'
        }
    
    @staticmethod
    def jetson_commands():
        """Jetson özel komutları"""
        return {
            'check_cuda': 'nvcc --version 2>/dev/null || echo "CUDA not installed"',
            'check_tensorrt': 'python3 -c "import tensorrt; print(tensorrt.__version__)" 2>/dev/null || echo "TensorRT not available"',
            'check_zed_sdk': 'python3 -c "import pyzed.sl; print(\'ZED SDK available\')" 2>/dev/null || echo "ZED SDK not installed"',
            'gpu_status': 'nvidia-smi --query-gpu=temperature.gpu,power.draw,utilization.gpu --format=csv,noheader,nounits 2>/dev/null || echo "GPU info not available"',
            'jetson_model': 'cat /proc/device-tree/model 2>/dev/null || echo "Model info not available"',
            'start_zed_server': 'cd /home/nvidia && python3 zed_server.py &',
            'stop_zed_server': 'pkill -f zed_server.py'
        }
    
    @staticmethod
    def network_commands():
        """Ağ komutları"""
        return {
            'check_internet': 'ping -c 1 8.8.8.8 > /dev/null && echo "Internet OK" || echo "No internet"',
            'get_ip': 'hostname -I | awk \'{print $1}\'',
            'get_wifi_status': 'iwgetid -r 2>/dev/null || echo "Not connected to WiFi"',
            'list_network_interfaces': 'ip link show | grep -E "^[0-9]+" | cut -d: -f2 | tr -d \' \'',
            'check_ssh_status': 'systemctl is-active ssh',
            'get_network_usage': 'cat /proc/net/dev | grep -E "(eth|wlan)" | awk \'{print $1,$2,$10}\''
        }
    
    @staticmethod
    def file_operations():
        """Dosya işlem komutları"""
        return {
            'create_directory': 'mkdir -p {path}',
            'remove_file': 'rm -f {file}',
            'copy_file': 'cp {source} {destination}',
            'move_file': 'mv {source} {destination}',
            'change_permissions': 'chmod {permissions} {file}',
            'check_file_exists': 'test -f {file} && echo "exists" || echo "not found"',
            'get_file_size': 'stat -c%s {file} 2>/dev/null || echo "0"',
            'list_directory': 'ls -la {path}',
            'disk_space': 'du -sh {path} 2>/dev/null || echo "N/A"'
        }
    
    @staticmethod
    def process_management():
        """Süreç yönetimi komutları"""
        return {
            'list_processes': 'ps aux',
            'kill_process': 'kill -9 {pid}',
            'kill_process_by_name': 'pkill -f {name}',
            'check_process': 'pgrep -f {name} || echo "Not running"',
            'process_cpu_usage': 'ps -p {pid} -o %cpu,pid,cmd --no-headers 2>/dev/null || echo "Process not found"',
            'system_load': 'cat /proc/loadavg'
        }