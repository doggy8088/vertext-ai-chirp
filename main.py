import os
from dotenv import load_dotenv

from google.api_core.client_options import ClientOptions
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech

# 載入環境變數
load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")

def transcribe_chirp_auto_detect_language(
    audio_file: str,
    region: str = "us-central1",
) -> cloud_speech.RecognizeResponse:
    """Transcribe an audio file and auto-detect spoken language using Chirp.
    Please see https://cloud.google.com/speech-to-text/v2/docs/encoding for more
    information on which audio encodings are supported.
    Args:
        audio_file (str): Path to the local audio file to be transcribed.
        region (str): The region for the API endpoint.
    Returns:
        cloud_speech.RecognizeResponse: The response containing the transcription results.
    """
    # Instantiates a client
    client = SpeechClient(
        client_options=ClientOptions(
            api_endpoint=f"{region}-speech.googleapis.com",
        )
    )

    # Reads a file as bytes
    with open(audio_file, "rb") as f:
        audio_content = f.read()

    config = cloud_speech.RecognitionConfig(
        auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
        # Set language code to auto to detect language.
        language_codes=["auto"],
        model="chirp",
    )

    request = cloud_speech.RecognizeRequest(
        recognizer=f"projects/{PROJECT_ID}/locations/{region}/recognizers/_",
        config=config,
        content=audio_content,
    )

    # Transcribes the audio into text
    response = client.recognize(request=request)

    for result in response.results:
        print(f"Transcript: {result.alternatives[0].transcript}")
        print(f"Detected Language: {result.language_code}")

    return response

def transcribe_chirp(
    audio_file: str,
    language_code: str = "en-US",
    region: str = "us-central1",
) -> cloud_speech.RecognizeResponse:
    """Transcribes an audio file using the Chirp model of Google Cloud Speech-to-Text API.
    Args:
        audio_file (str): Path to the local audio file to be transcribed.
            Example: "resources/audio.wav"
        language_code (str): The language code to use for transcription.
            Default is "en-US".
        region (str): The region for the API endpoint.
            Default is "us-central1".
    Returns:
        cloud_speech.RecognizeResponse: The response from the Speech-to-Text API containing
        the transcription results.
    """
    # Instantiates a client
    client = SpeechClient(
        client_options=ClientOptions(
            api_endpoint=f"{region}-speech.googleapis.com",
        )
    )

    # Reads a file as bytes
    with open(audio_file, "rb") as f:
        audio_content = f.read()

    config = cloud_speech.RecognitionConfig(
        auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
        language_codes=[language_code],
        model="chirp",
    )

    request = cloud_speech.RecognizeRequest(
        recognizer=f"projects/{PROJECT_ID}/locations/{region}/recognizers/_",
        config=config,
        content=audio_content,
    )

    # Transcribes the audio into text
    response = client.recognize(request=request)

    for result in response.results:
        print(f"Transcript: {result.alternatives[0].transcript}")

    return response

def main():
    """
    示範如何先偵測語言，再根據偵測結果進行轉錄
    """
    audio_file = "audio_files/開啟 Google 瀏覽器.wav"

    print("步驟 1: 偵測音訊檔案的語言...")
    detect_response = transcribe_chirp_auto_detect_language(audio_file)

    # 從偵測結果中獲取語言代碼
    detected_language = None
    if detect_response.results:
        detected_language = detect_response.results[0].language_code
        print(f"偵測到的語言: {detected_language}")
    else:
        # Speech-to-Text V2 supported languages
        # https://cloud.google.com/speech-to-text/v2/docs/speech-to-text-supported-languages
        print("無法偵測語言，使用預設語言 (cmn-Hant-TW)")
        detected_language = "cmn-Hant-TW"

    detected_language = "en-US"
    audio_file = "audio_files/Open Google Chrome.wav"

    print("\n步驟 2: 使用指定的語言 en-US 進行精確轉錄...")
    transcribe_response = transcribe_chirp(
        audio_file,
        language_code=detected_language
    )

    detected_language = "cmn-Hant-TW"
    audio_file = "audio_files/開啟 Google 瀏覽器.wav"

    print("\n步驟 3: 使用指定的語言 cmn-Hant-TW 進行精確轉錄...")
    transcribe_response = transcribe_chirp(
        audio_file,
        language_code=detected_language
    )

    print("\n轉錄完成!")

    return transcribe_response

if __name__ == "__main__":
    main()
