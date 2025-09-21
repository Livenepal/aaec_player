import streamlit as st
from streamlit.components.v1 import html
import re

st.set_page_config(
    layout="wide",
    page_title="Live TV",
    page_icon="📺",
    initial_sidebar_state="auto"
)

# Add responsive CSS
st.markdown("""
<style>
    /* Mobile-first responsive design */
    @media (max-width: 768px) {
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        
        /* Make sidebar more mobile friendly */
        .css-1d391kg {
            width: 100%;
        }
        
        /* Adjust video container for mobile */
        .video-container {
            padding-bottom: 75% !important; /* More square aspect ratio for mobile */
        }
        
        /* Smaller text for mobile */
        .stMetric > div > div {
            font-size: 0.8rem;
        }
        
        /* Stack columns on mobile */
        .element-container .stColumns {
            flex-direction: column;
        }
    }
    
    @media (min-width: 769px) {
        /* Desktop styles */
        .video-container {
            padding-bottom: 56.25% !important; /* 16:9 aspect ratio for desktop */
        }
    }
    
    /* General improvements */
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Video player improvements */
    #player-container {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }
    
    /* Sidebar improvements */
    .css-1d391kg {
        background: linear-gradient(145deg, #f0f2f6, #ffffff);
    }
    
    /* Hide Streamlit menu and footer on mobile */
    @media (max-width: 768px) {
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    }
</style>
""", unsafe_allow_html=True)

st.title("Live TV")

# Read M3U8 content from file
import os

# Try multiple possible locations for the M3U file
possible_paths = [
    'list.m3u',  # Current directory
    './list.m3u',  # Explicit current directory
    os.path.join(os.path.dirname(__file__), 'list.m3u'),  # Same directory as script
    'data/list.m3u',  # Data subdirectory
    './data/list.m3u',  # Explicit data subdirectory
]

m3u_content = None
found_file = None

for file_path in possible_paths:
    if not isinstance(file_path, str):
        continue
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            m3u_content = file.read()
            found_file = file_path
            break
    except FileNotFoundError:
        continue
    except Exception as e:
        st.warning(f"Error reading {file_path}: {e}")
        continue

if m3u_content is None:
    st.error("""
    **M3U file not found!** 
    
    Please ensure your `list.m3u` file is uploaded to your repository in one of these locations:
    - Root directory: `list.m3u`
    - Data folder: `data/list.m3u`
    
    **For Streamlit Cloud deployment:**
    1. Upload your `list.m3u` file to your GitHub repository
    2. Make sure it's in the same directory as `main.py`
    3. Redeploy your app
    
    **Current working directory:** `{os.getcwd()}`
    
    **Files in current directory:** 
    """)
    
    # List current directory contents for debugging
    try:
        files = os.listdir('.')
        st.write("📁 Files found:", files)
    except:
        st.write("Could not list directory contents")
    
    st.stop()


# Function to parse M3U content into a dictionary with categories
def parse_m3u_content(content):
    channels = {}
    categories = {}
    clean_channels = {}  # For display without category prefix
    lines = content.strip().split('\n')
    current_channel_name = None
    current_category = "General"
    channel_number = 1
    
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
            # Create user-friendly channel name with number
            clean_name = f"{channel_number:02d}. {current_channel_name}"
            full_channel_name = f"[{current_category}] {clean_name}"
            
            channels[full_channel_name] = line.strip()
            clean_channels[clean_name] = {
                'url': line.strip(),
                'category': current_category,
                'original_name': current_channel_name
            }
            categories[current_category].append(full_channel_name)
            current_channel_name = None
            channel_number += 1
            
    return channels, categories, clean_channels

# Parse the channels
channel_sources, channel_categories, clean_channels = parse_m3u_content(m3u_content)

if not channel_sources:
    st.error("No channels found in the provided M3U content. Please check the format.")
else:
    # Create responsive layout based on screen size
    # Use JavaScript to detect mobile and store in session state
    mobile_detection_script = """
    <script>
        function isMobile() {
            return window.innerWidth <= 768;
        }
        
        // Send mobile status to parent
        if (typeof(parent) !== 'undefined' && parent.postMessage) {
            parent.postMessage({
                type: 'mobile_detection',
                isMobile: isMobile()
            }, '*');
        }
    </script>
    """
    st.components.v1.html(mobile_detection_script, height=0)
    
    # Initialize mobile state
    if 'is_mobile' not in st.session_state:
        st.session_state.is_mobile = False
    
    # Create adaptive layout
    is_mobile = st.session_state.get('is_mobile', False)
    
    if is_mobile:
        # Mobile layout - stack vertically
        # Channel selection at top
        st.subheader("📺 Select Channel")
        
        # Simplified category selection for mobile
        category_options = ["All"] + list(channel_categories.keys())
        selected_category = st.selectbox(
            "Category:",
            category_options,
            index=next((i for i, cat in enumerate(category_options) if cat == "SPORTS"), 0),
            key="mobile_category"
        )
        
        # Filter channels
        if selected_category == "All":
            available_channels = list(channel_sources.keys())
        else:
            available_channels = channel_categories[selected_category]
        
        # Mobile-friendly channel selector
        channel_names = [x.split('] ')[1] if '] ' in x else x for x in available_channels]
        
        # Find StarSports 1 HD as default for mobile
        default_mobile_index = 0
        for i, channel in enumerate(available_channels):
            channel_name = channel.split('] ')[1] if '] ' in channel else channel
            clean_channel_name = channel_name.split('. ', 1)[1] if '. ' in channel_name else channel_name
            if "StarSports 1 HD" in clean_channel_name:
                default_mobile_index = i
                break
        
        selected_index = st.selectbox(
            "Channel:",
            range(len(available_channels)),
            format_func=lambda x: channel_names[x],
            index=default_mobile_index,
            key="mobile_channel"
        )
        selected_channel_name = available_channels[selected_index]
        
        # Navigation buttons for mobile
        nav_col1, nav_col2, nav_col3 = st.columns(3)
        with nav_col1:
            if st.button("⬅️ Previous", disabled=selected_index == 0, use_container_width=True):
                st.session_state.mobile_channel = selected_index - 1
                st.rerun()
        with nav_col2:
            if st.button("🎲 Random", use_container_width=True):
                import random
                random_index = random.randint(0, len(available_channels) - 1)
                st.session_state.mobile_channel = random_index
                st.rerun()
        with nav_col3:
            if st.button("➡️ Next", disabled=selected_index == len(available_channels) - 1, use_container_width=True):
                st.session_state.mobile_channel = selected_index + 1
                st.rerun()
    
    else:
        # Desktop layout - use sidebar
        st.sidebar.header("📺 Channel Selection")
        st.sidebar.markdown("---")
        
        # Category filter with icons for desktop
        category_icons = {
            "SERIALS": "🎭",
            "SPORTS": "⚽",
            "MUSICS AND SERIES": "🎵",
            "Cartoon": "🎨",
            "Movies": "🎬",
            "Danzer and Wildlife": "🦁",
            "NEPALI": "🇳🇵"
        }
        
        category_options = ["All"] + list(channel_categories.keys())
        category_display = []
        for cat in category_options:
            if cat == "All":
                category_display.append("🌐 All Categories")
            else:
                icon = category_icons.get(cat, "📻")
                category_display.append(f"{icon} {cat}")
        
        selected_category_display = st.sidebar.selectbox(
            "Filter by category:",
            category_display,
            index=next((i for i, cat in enumerate(category_options) if cat == "SPORTS"), 0)
        )
        
        selected_category = category_options[category_display.index(selected_category_display)]
        st.sidebar.markdown("---")
        
        # Filter channels based on category
        if selected_category == "All":
            available_channels = list(channel_sources.keys())
        else:
            available_channels = channel_categories[selected_category]
        
        st.sidebar.write(f"**{len(available_channels)} channels available**")
        
        # Find StarSports 1 HD as default
        default_index = 0
        for i, channel in enumerate(available_channels):
            channel_name = channel.split('] ')[1] if '] ' in channel else channel
            clean_channel_name = channel_name.split('. ', 1)[1] if '. ' in channel_name else channel_name
            if "StarSports 1 HD" in clean_channel_name:
                default_index = i
                break
        
        selected_channel_name = st.sidebar.radio(
            "Choose a channel to watch:",
            available_channels,
            index=default_index,
            format_func=lambda x: x.split('] ')[1] if '] ' in x else x
        )
        
        # Quick access for desktop
        st.sidebar.markdown("---")
        st.sidebar.subheader("⭐ Quick Access")
        
        if st.sidebar.button("🔄 Reload Player", use_container_width=True):
            st.rerun()
        
        if 'selected_channel' in st.session_state and st.session_state.selected_channel in available_channels:
            selected_channel_name = st.session_state.selected_channel

    # Get the URL for the selected channel
    selected_channel_url = channel_sources[selected_channel_name]
    
    # Extract clean channel name for display
    display_name = selected_channel_name.split('] ')[1] if '] ' in selected_channel_name else selected_channel_name
    
    # Create main header with channel info
    st.subheader(f"📺 Now Playing: **{display_name}**")
    
    # Quick access channels - moved from sidebar to main page
    if not is_mobile:  # Only show on desktop
        st.markdown("**⭐ Quick Access**")
        
        # Define preferred sports channels for quick access
        preferred_channels = [
            "StarSports 1 HD",
            "StarSports 2 HD", 
            "StarSports 3 HD",
            "StarSports SELECT 1 HD",
            "StarSports SELECT 2 HD",
            "StarSports SELECT 1",
            "StarSports SELECT 2",
            "Sony Ten 1 HD",
            "Sony Ten 2 HD",
            "Sony Ten 3 HD",
            "StarSports 1 HD HINDI"
        ]
        
        # Find matching channels from all available channels
        quick_access_channels = []
        for channel_full in channel_sources.keys():
            channel_name = channel_full.split('] ')[1] if '] ' in channel_full else channel_full
            # Remove channel number prefix for matching
            clean_channel_name = channel_name.split('. ', 1)[1] if '. ' in channel_name else channel_name
            
            if clean_channel_name in preferred_channels:
                display_name = clean_channel_name
                if len(display_name) > 15:
                    display_name = display_name[:12] + "..."
                quick_access_channels.append((channel_full, display_name))
        
        # Display up to 6 quick access channels
        if quick_access_channels:
            num_cols = min(6, len(quick_access_channels))
            quick_cols = st.columns(num_cols)
            for i, (full_name, display_name_short) in enumerate(quick_access_channels[:6]):
                with quick_cols[i]:
                    if st.button(display_name_short, key=f"main_quick_{i}", use_container_width=True):
                        st.session_state.selected_channel = full_name
                        st.rerun()
        
        # Add small navigation buttons below quick access
        current_index = available_channels.index(selected_channel_name)
        nav_spacer1, nav_col1, nav_spacer2, nav_col2, nav_spacer3 = st.columns([2, 0.5, 0.2, 0.5, 2])
        
        with nav_col1:
            if st.button("⬅️", disabled=current_index == 0, key="nav_prev", help="Previous channel"):
                prev_channel = available_channels[current_index - 1]
                st.session_state.selected_channel = prev_channel
                st.rerun()
        with nav_col2:
            if st.button("➡️", disabled=current_index == len(available_channels) - 1, key="nav_next", help="Next channel"):
                next_channel = available_channels[current_index + 1]
                st.session_state.selected_channel = next_channel
                st.rerun()
    # HLS.js integration for robust HLS playback with mobile responsiveness
    mobile_aspect_ratio = "75%" if is_mobile else "56.25%"
    
    hls_player_html = f"""
    <div id="player-container" class="video-container" style="position: relative; padding-bottom: {mobile_aspect_ratio}; height: 0; overflow: hidden; max-width: 100%; background-color: #000; border-radius: 12px; box-shadow: 0 8px 32px rgba(0,0,0,0.3);">
        <video id="video" controls style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border-radius: 12px;"></video>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/hls.js@1.4.14/dist/hls.min.js"></script>
    <script>
      console.log('Loading channel: {selected_channel_name}');
      console.log('URL: {selected_channel_url}');
      
      var video = document.getElementById('video');
      
      // Mobile-specific optimizations
      var isMobile = window.innerWidth <= 768;
      if (isMobile) {{
        video.setAttribute('playsinline', true);
        video.setAttribute('webkit-playsinline', true);
      }}
      
      // Destroy any existing HLS instance
      if (window.currentHls) {{
        window.currentHls.destroy();
        window.currentHls = null;
      }}
      
      // Reset video element
      video.pause();
      video.src = '';
      video.load();
      
      var hlsConfig = {{
        debug: false,
        enableWorker: true,
        lowLatencyMode: false,
        backBufferLength: 30,
        maxBufferLength: 30,
        maxMaxBufferLength: 60,
        startLevel: -1,
        autoStartLoad: true
      }};
      
      if (Hls.isSupported()) {{
        var hls = new Hls(hlsConfig);
        window.currentHls = hls;

        hls.on(Hls.Events.MANIFEST_PARSED, function() {{
          console.log('Manifest parsed, starting playback');
          setTimeout(() => {{
            video.play().catch(e => {{
              console.log('Autoplay failed, user interaction required:', e);
            }});
          }}, 500);
        }});
        
        hls.on(Hls.Events.FRAG_LOADED, function() {{
          console.log('First fragment loaded, attempting play');
          setTimeout(() => {{
            if (video.paused) {{
              video.play().catch(e => {{
                console.log('Autoplay failed on fragment load:', e);
              }});
            }}
          }}, 100);
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
        
        // Load source and attach media
        hls.loadSource('{selected_channel_url}');
        hls.attachMedia(video);
        
        // Additional autoplay attempt after attachment
        setTimeout(() => {{
          if (video.paused && video.readyState >= 2) {{
            console.log('Attempting autoplay after media attachment');
            video.play().catch(e => {{
              console.log('Post-attachment autoplay failed:', e);
            }});
          }}
        }}, 1000);
        
      }} else if (video.canPlayType('application/vnd.apple.mpegurl')) {{
        console.log('Using native HLS support');
        video.src = '{selected_channel_url}';
        video.addEventListener('loadedmetadata', function() {{
          setTimeout(() => {{
            video.play().catch(e => console.log('Autoplay failed:', e));
          }}, 500);
        }});
        video.addEventListener('canplay', function() {{
          setTimeout(() => {{
            if (video.paused) {{
              video.play().catch(e => console.log('Can play autoplay failed:', e));
            }}
          }}, 200);
        }});
      }} else {{
        console.error('HLS not supported');
        document.getElementById('player-container').innerHTML = '<p style="color: white; text-align: center; padding: 20px;">Your browser does not support HLS video playback. Please try using Chrome, Firefox, or Safari.</p>';
      }}
      
      // Add general video event listeners for better autoplay handling
      video.addEventListener('loadeddata', function() {{
        console.log('Video loaded data, attempting autoplay');
        setTimeout(() => {{
          if (video.paused) {{
            video.play().catch(e => console.log('Loadeddata autoplay failed:', e));
          }}
        }}, 300);
      }});
      
      video.addEventListener('canplaythrough', function() {{
        console.log('Video can play through, attempting autoplay');
        setTimeout(() => {{
          if (video.paused) {{
            video.play().catch(e => console.log('Canplaythrough autoplay failed:', e));
          }}
        }}, 100);
      }});
      
      // Add click to play functionality
      video.addEventListener('click', function() {{
        if (video.paused) {{
          video.play();
        }} else {{
          video.pause();
        }}
      }});
      
      // Try autoplay after a short delay when everything is loaded
      setTimeout(() => {{
        if (video.paused && video.readyState >= 2) {{
          console.log('Final autoplay attempt');
          video.play().catch(e => {{
            console.log('Final autoplay failed, user interaction required:', e);
            // Show a subtle play button overlay if autoplay fails
            var playButton = document.createElement('div');
            playButton.innerHTML = '▶️ Click to Play';
            playButton.style.cssText = 'position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: rgba(0,0,0,0.7); color: white; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-size: 16px; z-index: 1000;';
            playButton.onclick = function() {{
              video.play();
              playButton.remove();
            }};
            document.getElementById('player-container').appendChild(playButton);
          }});
        }}
      }}, 2000);
      
      // Mobile-specific touch controls
      if (isMobile) {{
        var touchStartTime = 0;
        video.addEventListener('touchstart', function(e) {{
          touchStartTime = Date.now();
        }});
        
        video.addEventListener('touchend', function(e) {{
          var touchDuration = Date.now() - touchStartTime;
          if (touchDuration < 200) {{ // Quick tap
            if (video.paused) {{
              video.play();
            }} else {{
              video.pause();
            }}
          }}
        }});
      }}
    </script>
    """
    st.components.v1.html(hls_player_html, height=620, scrolling=False)
    
    # Responsive controls section
    if not is_mobile:
        # Desktop controls - full feature set

        
        # Footer
        st.markdown("---")
        st.caption(" AAEC Custom Player")
  
    
    else:
        # Mobile controls - simplified
        st.markdown("---")
        
        mobile_control_col1, mobile_control_col2 = st.columns(2)
        with mobile_control_col1:
            if st.button("🔄 Reload", use_container_width=True):
                st.rerun()
        with mobile_control_col2:
            if st.button("📊 Info", use_container_width=True):
                st.info(f"**{display_name}** | Category: {selected_category} | {current_index + 1}/{len(available_channels)}")
        
        # Simplified footer for mobile
        st.markdown("---")
        st.caption(f"📺 {display_name} | {selected_category} | {current_index + 1}/{len(available_channels)}")
    

    
