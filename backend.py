from flask import Flask, request, send_file, jsonify
from flask import after_this_request
import yt_dlp
import os
import uuid
import unicodedata

app = Flask(__name__)
DOWNLOAD_FOLDER = 'Descargas'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

@app.route('/Descargas', methods=['POST'])
def download_audio():
    data = request.get_json()
    url = data.get('url')
    if not url:
        return jsonify({'error': 'No se proporcionó URL'}), 400

    try:
        # Obtener metadata sin descargar aún
        with yt_dlp.YoutubeDL({'quiet': True, 'cookiefile': 'cookies.txt'}) as ydl:
            info = ydl.extract_info(url, download=False)
            video_title = info.get('title', str(uuid.uuid4()))
            thumbnail_url = info.get('thumbnail', '')

        # Normalizar título para usarlo como nombre de archivo seguro
        nfkd = unicodedata.normalize('NFKD', video_title)
        ascii_title = "".join([c for c in nfkd if c.isalnum() or c in (' ', '_', '-')])
        ascii_title = ascii_title.replace(' ', '_') or str(uuid.uuid4())
        filename = f"{ascii_title}.mp3"
        output_path = os.path.join(DOWNLOAD_FOLDER, filename)

        # También generar nombre ASCII seguro para enviar al frontend
        safe_ascii = ''.join([c for c in ascii_title if c.isascii()]) or str(uuid.uuid4())
        safe_filename = f"{safe_ascii}.mp3"

        # Opciones para yt-dlp
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'cookiefile': 'cookies.txt',  # <-- cookies para evitar login/captcha
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'ffmpeg_location': '/usr/bin/ffmpeg',
            'quiet': False,
            'verbose': True,
        }

        # Descargar audio
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Verificar que el archivo se generó
        final_path = output_path
        if not os.path.exists(final_path):
            alt_path = output_path + '.mp3'
            if os.path.exists(alt_path):
                final_path = alt_path
                filename = filename + '.mp3'
            else:
                return jsonify({'error': f'No se generó el archivo: {output_path} ni {alt_path}'}), 500

        # Eliminar el archivo después de enviarlo
        @after_this_request
        def remove_file(response):
            try:
                if os.path.exists(final_path):
                    os.remove(final_path)
                alt_path = output_path if final_path != output_path else output_path + '.mp3'
                if os.path.exists(alt_path):
                    os.remove(alt_path)
            except Exception as e:
                print(f"Error al borrar archivo: {e}")
            return response

        # Enviar archivo
        response = send_file(final_path, as_attachment=True, download_name=safe_filename)
        response.headers['X-Audio-Filename'] = safe_filename
        if thumbnail_url:
            response.headers['X-Audio-Thumbnail'] = thumbnail_url
        return response

    except Exception as e:
        print(f"Error al descargar: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
