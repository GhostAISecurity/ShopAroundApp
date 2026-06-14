import re

# Read the current dashboard HTML from the existing route
with open("shoparound_professional.py", "r") as f:
    content = f.read()

# Check if Mmapateng widget already exists
if "mmapateng-chat" in content or "Mmapateng" in content:
    print("✅ Mmapateng already in dashboard")
else:
    # Find the dashboard HTML and add Mmapateng widget
    mmapateng_widget = '''
    <!-- Mmapateng Chat Widget -->
    <div class="mmapateng-chat" style="position: fixed; bottom: 20px; right: 20px; z-index: 1000;">
        <div class="chat-button" onclick="toggleMmapatengChat()" style="width: 60px; height: 60px; background: linear-gradient(135deg, #7c3aed, #ec4899); border-radius: 50%; display: flex; align-items: center; justify-content: center; cursor: pointer; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
            <span style="font-size: 28px;">💬</span>
        </div>
        <div class="chat-window" id="mmapatengChatWindow" style="position: absolute; bottom: 80px; right: 0; width: 350px; height: 500px; background: white; border-radius: 20px; display: none; flex-direction: column; overflow: hidden; box-shadow: 0 10px 40px rgba(0,0,0,0.2);">
            <div class="chat-header" style="background: linear-gradient(135deg, #7c3aed, #ec4899); color: white; padding: 15px; display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 20px;">🧠</span>
                    <span style="font-weight: bold;">Mmapateng AI</span>
                </div>
                <span onclick="toggleMmapatengChat()" style="cursor: pointer;">✕</span>
            </div>
            <div class="chat-messages" id="mmapatengMessages" style="flex: 1; padding: 15px; overflow-y: auto; background: #f8f9fa;">
                <div class="message bot" style="margin-bottom: 10px; display: flex; justify-content: flex-start;">
                    <div class="message-content" style="max-width: 80%; padding: 10px 15px; border-radius: 20px; background: white; color: #333; border-bottom-left-radius: 5px;">
                        🫶 Yoh! I'm Mmapateng, your AI shopping assistant! Ask me about budgets (R200), prices, or deals!
                    </div>
                </div>
            </div>
            <div class="chat-input" style="padding: 15px; background: white; border-top: 1px solid #eee; display: flex; gap: 10px;">
                <input type="text" id="mmapatengInput" placeholder="Ask Mmapateng..." style="flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 25px; outline: none;" onkeypress="if(event.key==='Enter') sendMmapatengMessage()">
                <button onclick="sendMmapatengMessage()" style="background: linear-gradient(135deg, #7c3aed, #ec4899); color: white; border: none; padding: 10px 20px; border-radius: 25px; cursor: pointer;">Send</button>
            </div>
        </div>
    </div>
    
    <script>
        function toggleMmapatengChat() {
            const window = document.getElementById('mmapatengChatWindow');
            if (window) window.style.display = window.style.display === 'flex' ? 'none' : 'flex';
        }
        
        async function sendMmapatengMessage() {
            const input = document.getElementById('mmapatengInput');
            const message = input.value.trim();
            if (!message) return;
            
            const messagesDiv = document.getElementById('mmapatengMessages');
            messagesDiv.innerHTML += `<div class="message user" style="margin-bottom: 10px; display: flex; justify-content: flex-end;">
                <div class="message-content" style="max-width: 80%; padding: 10px 15px; border-radius: 20px; background: linear-gradient(135deg, #7c3aed, #ec4899); color: white; border-bottom-right-radius: 5px;">${escapeHtml(message)}</div>
            </div>`;
            input.value = '';
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
            
            try {
                const response = await fetch('/api/mmapateng/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: message })
                });
                const data = await response.json();
                messagesDiv.innerHTML += `<div class="message bot" style="margin-bottom: 10px; display: flex; justify-content: flex-start;">
                    <div class="message-content" style="max-width: 80%; padding: 10px 15px; border-radius: 20px; background: white; color: #333; border-bottom-left-radius: 5px;">${escapeHtml(data.response)}</div>
                </div>`;
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            } catch (error) {
                messagesDiv.innerHTML += `<div class="message bot" style="margin-bottom: 10px; display: flex; justify-content: flex-start;">
                    <div class="message-content" style="max-width: 80%; padding: 10px 15px; border-radius: 20px; background: white; color: #333;">🫶 Yoh! Let me try again. What can I help you with?</div>
                </div>`;
            }
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    </script>
    <style>
        .mmapateng-chat .chat-window { display: none; }
        .mmapateng-chat .chat-window.open { display: flex; }
    </style>
    '''
    
    # Find where to insert the widget (before the closing body tag in the HTML)
    # Look for the dashboard HTML section
    if 'def dashboard():' in content:
        # Find the dashboard function and add widget to its HTML
        pattern = r'(def dashboard\(\):.*?return render_template_string\([\'"])(.*?)([\'"]\))'
        def replace_func(match):
            prefix = match.group(1)
            html_content = match.group(2)
            suffix = match.group(3)
            # Add widget before closing body tag
            if '</body>' in html_content:
                new_html = html_content.replace('</body>', f'{mmapateng_widget}</body>')
                return f'{prefix}{new_html}{suffix}'
            return match.group(0)
        
        new_content = re.sub(pattern, replace_func, content, flags=re.DOTALL)
        
        if new_content != content:
            with open("shoparound_professional.py", "w") as f:
                f.write(new_content)
            print("✅ Mmapateng widget added to dashboard")
        else:
            print("⚠️ Could not add widget - dashboard HTML not found")
    else:
        print("⚠️ Dashboard route not found")
    
    # Also ensure Mmapateng API routes exist
    if "mmapateng" not in content:
        print("⚠️ Mmapateng API not found. Make sure mmapateng_simple.py is available")
    else:
        print("✅ Mmapateng API ready")

print("="*50)
print("Mmapateng added to your existing dashboard!")
print("Open: http://localhost:5000/dashboard")
print("="*50)
