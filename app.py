import streamlit as st
import yt_to_pdf

# Set up the page configuration
st.set_page_config(page_title="YouTube to PDF Converter 🎥➡️📄", layout="centered")

# Sidebar Instructions using headers and markdown for clear hierarchy
st.sidebar.title("Instructions 📋")
st.sidebar.markdown(
    """
    **Step 1:** Enter a valid YouTube URL 📺.
    
    **Step 2:** Click the **Convert** button 🔄.
    
    **Step 3:** Wait for the video to be processed ⏳.
    
    **Step 4:** Download your generated PDF 📥.
    """
)

# Main content area with different text sizes via built-in components
st.title("YouTube Video to PDF Converter")
st.write("")
st.write("This tool extracts key frames from your YouTube video and compiles them into a PDF file ✨")
st.write("Simply enter the URL below and click **Convert**.")

st.write("")
# Input field for YouTube URL
youtube_url = st.text_input("Enter YouTube URL:")

# Button and conversion logic with status messages
if st.button("Convert"):
    if not youtube_url.strip():
        st.error("Please enter a valid YouTube URL! ❌")
    else:
        with st.spinner("Processing video, please wait... ⏳"):
            try:
                pdf_bytes, pdf_filename = yt_to_pdf.convert_youtube_to_pdf(youtube_url)
                st.success("PDF generated successfully! ✅")
                st.download_button("Download PDF 📥", data=pdf_bytes, file_name=pdf_filename, mime="application/pdf")
            except Exception as e:
                st.error(f"An error occurred: {e} ❌")

# Footer separator
st.markdown("---")
