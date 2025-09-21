import streamlit as st
from streamlit.components.v1 import html
import re

st.set_page_config(layout="wide")

st.title("My Custom M3U8 TV Player")

# Read M3U8 content from file
try:
    with open('/Users/suraj/Desktop/aaec_player/list.m3u', 'r', encoding='utf-8') as file:
        m3u_content = file.read()
except FileNotFoundError:
    st.error("list.m3u file not found! Please make sure the file exists in the correct location.")
    st.stop()
except Exception as e:
    st.error(f"Error reading list.m3u file: {e}")
    st.stop()

# Function to parse M3U content into a dictionary with categories
def parse_m3u_content(content):
    channels = {}
    categories = {}
    lines = content.strip().split('\n')
    current_channel_name = None
    current_category = "General"
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines and comments that aren't channel info
        if not line or line.startswith('//') or line == '#EXTM3U':
            continue
            
        # Check for category headers
        if line.startswith('#========') and line.endswith('=========='):
            current_category = line.replace('#========', '').replace('==========', '').strip()
            if current_category not in categories:
                categories[current_category] = []
            continue
            
        # Check for channel info
        if line.startswith('#EXTINF:'):
            match = re.search(r'#EXTINF:0,(.*)', line)
            if match:
                current_channel_name = match.group(1).strip()
        elif line.startswith('http') and current_channel_name:
            # Add category prefix to channel name for organization
            full_channel_name = f"[{current_category}] {current_channel_name}"
            channels[full_channel_name] = line.strip()
            categories[current_category].append(full_channel_name)
            current_channel_name = None # Reset for the next channel
            
    return channels, categories

# Parse the channels
channel_sources, channel_categories = parse_m3u_content(m3u_content)

if not channel_sources:
    st.error("No channels found in the provided M3U content. Please check the format.")
else:
    # Create a sidebar for channel selection
    st.sidebar.header("Select a Channel")
    
    # Category filter
    selected_category = st.sidebar.selectbox(
        "Filter by category:",
        ["All"] + list(channel_categories.keys())
    )
    
    # Filter channels based on category
    if selected_category == "All":
        available_channels = list(channel_sources.keys())
    else:
        available_channels = channel_categories[selected_category]
    
    selected_channel_name = st.sidebar.radio(
        "Choose a channel to watch:",
        available_channels
    )

    # Get the URL for the selected channel
    selected_channel_url = channel_sources[selected_channel_name]

    st.subheader(f"Now playing: **{selected_channel_name}**")

    # HLS.js integration for robust HLS playback
    hls_player_html = f"""
    <div id="player-container" style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; background-color: #000;">
        <video id="video" controls muted style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></video>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/hls.js@1.4.14/dist/hls.min.js"></script>
    <script>
      console.log('Loading channel: {selected_channel_name}');
      console.log('URL: {selected_channel_url}');
      
      var video = document.getElementById('video');
      
      // Destroy any existing HLS instance
      if (window.currentHls) {{
        window.currentHls.destroy();
        window.currentHls = null;
      }}
      
      // Reset video element
      video.pause();
      video.src = '';
      video.load();
      
      var hls = new Hls({{
        debug: false,
        enableWorker: true,
        lowLatencyMode: false,
        backBufferLength: 30,
        maxBufferLength: 30,
        maxMaxBufferLength: 60,
        startLevel: -1,
        autoStartLoad: true,
        capLevelToPlayerSize: true
      }});
      
      window.currentHls = hls;

      // Check if HLS.js is supported
      if (Hls.isSupported()) {{
        console.log('HLS.js is supported');
        
        hls.on(Hls.Events.MANIFEST_PARSED, function() {{
          console.log('Manifest parsed, starting playbook');
          video.play().catch(e => {{
            console.log('Autoplay failed, user interaction required:', e);
          }});
        }});
        
        hls.on(Hls.Events.ERROR, function (event, data) {{
          console.error('HLS error:', data);
          if (data.fatal) {{
            switch(data.type) {{
              case Hls.ErrorTypes.NETWORK_ERROR:
                console.error("Network error, trying to recover");
                setTimeout(() => {{
                  if (hls) {{
                    hls.startLoad();
                  }}
                }}, 1000);
                break;
              case Hls.ErrorTypes.MEDIA_ERROR:
                console.error("Media error, trying to recover");
                setTimeout(() => {{
                  if (hls) {{
                    hls.recoverMediaError();
                  }}
                }}, 1000);
                break;
              default:
                console.error("Fatal error, destroying HLS instance");
                hls.destroy();
                window.currentHls = null;
                // Try direct video source as fallback
                video.src = '{selected_channel_url}';
                video.play().catch(e => console.log('Direct playback failed:', e));
                break;
            }}
          }}
        }});
        
        hls.on(Hls.Events.LEVEL_LOADED, function(event, data) {{
          console.log('Level loaded successfully');
        }});
        
        // Load the source after setting up event listeners
        hls.loadSource('{selected_channel_url}');
        hls.attachMedia(video);
        
      }} else if (video.canPlayType('application/vnd.apple.mpegurl')) {{
        console.log('Using native HLS support');
        video.src = '{selected_channel_url}';
        video.addEventListener('loadedmetadata', function() {{
          video.play().catch(e => console.log('Autoplay failed:', e));
        }});
      }} else {{
        console.error('HLS not supported');
        document.getElementById('player-container').innerHTML = '<p style="color: white; text-align: center; padding: 20px;">Your browser does not support HLS video playback. Please try using Chrome, Firefox, or Safari.</p>';
      }}
      
      // Add click to play functionality
      video.addEventListener('click', function() {{
        if (video.paused) {{
          video.play();
        }} else {{
          video.pause();
        }}
      }});
      
      // Add loading indicator
      video.addEventListener('loadstart', function() {{
        console.log('Loading started');
      }});
      
      video.addEventListener('canplay', function() {{
        console.log('Video can start playing');
      }});
      
      video.addEventListener('playing', function() {{
        console.log('Video is playing');
      }});
      
      video.addEventListener('error', function(e) {{
        console.error('Video error:', e);
      }});
    </script>
    """
    st.components.v1.html(hls_player_html, height=600, scrolling=False)

    # Add a manual play button
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        if st.button("▶️ Click to Play", use_container_width=True):
            st.rerun()

    st.markdown("---")
    st.info(f"The URL for the current channel is: `{selected_channel_url}`")
    st.write("Built with Streamlit and HLS.js!")