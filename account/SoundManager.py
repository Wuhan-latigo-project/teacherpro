# SoundManager.py - Using sound_player.exe for WAV files
import os
import subprocess
import threading

class SoundManager:
    """Manages sound notifications for user interactions using sound_player.exe"""
    
    def __init__(self):
        # Map sound names to WAV files
        self.sound_files = {
            "click": "STREAMING-notification-alert-pop-up-ding-soundroll-1-00-02.wav",
            "success": "STREAMING-correct-bell-twinkle-jam-fx-1-00-05.wav",
            "error": "STREAMING-phone-alert-marimba-bubble-om-fx-1-00-01.wav",
            "notification": "STREAMING-notification-bells-sms-received-jam-fx-medium-1-00-01.wav",
            "upload": "STREAMING-happy-alert-chimes-danijel-zambo-1-1-00-03.wav",
            "edit": "STREAMING-bubble-pop-high-jam-fx-1-00-00.wav",
            "delete": "STREAMING-phone-alert-marimba-bubble-om-fx-1-00-01.wav",
            "login": "STREAMING-game-ui-level-unlock-om-fx-1-1-00-05.wav",
            "logout": "STREAMING-swipe-whoosh-bell-betacut-1-00-01.wav",
            "alert": "STREAMING-stream-alert-trap-beat-intro-gfx-sounds-1-00-04.wav",
            "message": "STREAMING-notification-bells-sms-received-jam-fx-medium-1-00-01.wav",
            "futuristic": "STREAMING-stream-alert-trap-beat-intro-gfx-sounds-1-00-04.wav"
        }
        
        # Paths
        self.sounds_path = "sounds"
        self.exe_path = "soundplayer/sound_player.exe"
        #path of the exe is in this dir ./soundplayer/sound_player.exe ,but i dont know how i can enter into the python code
        self
        
        
        print(f"📁 Sounds path: {self.sounds_path}")
        print(f"📁 EXE path: {self.exe_path}")
        
        self.check_sound_files()
        self.check_exe_file()
    
    def check_sound_files(self):
        """Check if sound files exist"""
        print("🔍 Checking sound files...")
        for sound_name, filename in self.sound_files.items():
            full_path = os.path.join(self.sounds_path, filename)
            if os.path.exists(full_path):
                print(f"✅ Found: {filename}")
            else:
                print(f"❌ NOT FOUND: {filename}")
    
    def check_exe_file(self):
        """Check if sound_player.exe exists"""
        if os.path.exists(self.exe_path):
            print(f"✅ Found: sound_player.exe")
        else:
            print(f"❌ ERROR: sound_player.exe not found at: {self.exe_path}")
            print("   Place sound_player.exe in the same directory as SoundManager.py")
    
    def play_sound(self, sound_name, async_mode=True):
        """Play a sound by name using sound_player.exe"""
        if sound_name not in self.sound_files:
            print(f"❌ Sound '{sound_name}' not found in mapping")
            return False
        
        # Check if sound_player.exe exists
        if not os.path.exists(self.exe_path):
            print(f"❌ Cannot play sound: sound_player.exe not found")
            return False
        
        sound_file = self.sound_files[sound_name]
        full_path = os.path.join(self.sounds_path, sound_file)
        
        if not os.path.exists(full_path):
            print(f"❌ Sound file not found: {full_path}")
            return False
        
        print(f"🔊 Attempting to play {sound_name} from: {full_path}")
        
        # Use sound_player.exe to play the sound
        if async_mode:
            # Play in background thread
            def play_thread():
                try:
                    # Use sound_player.exe with the file path
                    print(f"🎵 Starting {sound_name} in background...")
                    
                    # For Windows, use the EXE with CREATE_NO_WINDOW flag
                    process = subprocess.Popen(
                        [self.exe_path, full_path],
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        stdin=subprocess.PIPE
                    )
                    
                    # Don't wait for it to complete
                    print(f"✅ {sound_name} sound started in background (PID: {process.pid})")
                    return True
                    
                except Exception as e:
                    print(f"❌ Error playing sound with sound_player.exe: {e}")
                    return False
            
            thread = threading.Thread(target=play_thread, daemon=True)
            thread.start()
            return True
            
        else:
            # Play in main thread (blocking)
            try:
                print(f"🎵 Playing {sound_name}...")
                result = subprocess.run(
                    [self.exe_path, full_path],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    print(f"✅ {sound_name} sound played successfully")
                    return True
                else:
                    print(f"❌ sound_player.exe failed: {result.stderr}")
                    return False
            except subprocess.TimeoutExpired:
                print(f"⚠️  {sound_name} sound player timed out (still playing in background)")
                return True
            except Exception as e:
                print(f"❌ Error playing sound: {e}")
                return False
    
    # Convenience methods
    def play_click(self):
        """Play click sound"""
        return self.play_sound("click")
    
    def play_success(self):
        """Play success sound"""
        return self.play_sound("success")
    
    def play_error(self):
        """Play error sound"""
        return self.play_sound("error")
    
    def play_notification(self):
        """Play notification sound"""
        return self.play_sound("notification")
    
    def play_upload(self):
        """Play upload sound"""
        return self.play_sound("upload")
    
    def play_edit(self):
        """Play edit sound"""
        return self.play_sound("edit")
    
    def play_login(self):
        """Play login sound"""
        return self.play_sound("login")
    
    def play_logout(self):
        """Play logout sound"""
        return self.play_sound("logout")
    
    def play_alert(self):
        """Play alert sound"""
        return self.play_sound("alert")
    
    def play_message(self):
        """Play message sound"""
        return self.play_sound("message")

# Create global instance
sound_manager = SoundManager()