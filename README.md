# 使用 Google Chirp 通用語音模型進行高品質語音識別與文字轉錄

最近研究了多套語音轉文字的模型，今天這篇文章我打算來分享一套由 Google 發展的 [Chirp](https://cloud.google.com/speech-to-text/v2/docs/chirp-model) 通用語音模型 ([Google USM](https://arxiv.org/pdf/2303.01037))，該模型能夠在單一模型中統一處理多種語言的數據，為使用者提供更精確、更靈活的語音識別體驗。與傳統語音模型不同，Chirp 能夠處理更大塊的語音片段，雖然這意味著它可能不適合真正的即時應用場景，但在處理短音頻(小於1分鐘)和長音頻(1分鐘至8小時)時，其表現卻十分出色。

![An abstract digital illustration representing Google's Chirp speech model for high-quality speech recognition.](https://github.com/user-attachments/assets/9505a2c2-4b2c-4674-b81a-7f269e468f24)

[Chirp](https://cloud.google.com/speech-to-text/v2/docs/chirp-model) 模型的一大亮點是其支援語言無關的音頻轉錄功能，能夠自動推斷音頻文件中的口語語言並將其添加到結果中，這對於處理多語言環境下的語音識別任務具有重要意義。此外，Chirp 還支援自動標點和詞時間戳等實用功能，進一步提升了轉錄結果的可讀性和實用性。

接下來我會帶大家走一遍 Chirp 模型的使用方式：

## 1. 初始化 Google Cloud 環境

開始的步驟比較麻煩，需要對 Google Cloud 環境有點認識才有辦法設定好：

1. 你要先建立一個 [Google Cloud Console](https://console.cloud.google.com/) 的專案
2. 再到 [專案選擇器](https://console.cloud.google.com/projectselector2/home/dashboard) 選擇一個現有的專案
3. 還必須[確保你的 Google Cloud 專案已啟用計費](https://cloud.google.com/billing/docs/how-to/verify-billing-enabled#confirm_billing_is_enabled_on_a_project)
4. 最後還要手動啟用 [Cloud Speech-to-Text API API](https://console.cloud.google.com/flows/enableapi?apiid=speech.googleapis.com,) 才能開始使用 Chirp 服務
5. 如果你不是管理者，可能要請人幫你授權 `Cloud Speech Administrator` 角色
6. 安裝 `gcloud` 命令列工具 ([Install the gcloud CLI](https://cloud.google.com/sdk/docs/install))
7. 初始化 gcloud CLI 執行環境

    ```sh
    gcloud init
    ```

8. 以系統管理員權限開啟另開一個 Command Prompt 視窗並執行更新命令

    ```sh
    gcloud components update
    ```

9. 建立本地認證憑證 (ADC)

    ```sh
    gcloud auth application-default login
    ```

    這個命令可以讓你取得**應用程式預設憑證** ([Application Default Credentials](https://cloud.google.com/docs/authentication/application-default-credentials))，簡稱 `ADC` 的東西，他可以讓你之後的程式都不需要特別處理金鑰或認證等設定，讓你輕鬆地對 Google API 進行身份驗證並向這些 API 發送請求，可以大幅簡化應用程式的開發流程。

    > 如果你使用 Cloud Shell 操作的話，就不需這一步驟，因為 ADC 已經內建。

## 2. 建立 Python 虛擬環境

在命令提示字元中執行以下指令來建立一個 Python 虛擬環境：

```bash
python -m venv .venv
```

若使用 Visual Studio Code 開發環境，也可以透過 VS Code 的 GUI 介面建立虛擬環境。詳情請見: [Python environments in VS Code](https://code.visualstudio.com/docs/python/environments) 文件的 [Creating environments](https://code.visualstudio.com/docs/python/environments#_creating-environments) 小節。

啟動虛擬環境：

- **Windows 系統**

  Command Prompt

  ```bat
  .venv\Scripts\activate
  ```

  PowerShell

  ```ps1
  . .\.venv\Scripts\activate.ps1
  ```

- **macOS/Linux 系統**

  ```bash
  source .venv/bin/activate
  ```

## 3. 安裝必要套件

[Chirp](https://cloud.google.com/speech-to-text/v2/docs/chirp-model) 被整合在 Google Cloud 的 [Speech-to-Text API v2](https://cloud.google.com/speech-to-text/v2/docs) 之中，所以我們需要安裝 `google-cloud-speech` 套件。在 Python 虛擬環境中，可以使用 `pip` 安裝：

```bash
pip install --upgrade google-cloud-speech
```

> [Speech-to-Text client libraries](https://cloud.google.com/speech-to-text/v2/docs/libraries#client-libraries-install-python)

建立 `requirements.txt` 檔案：

```bash
pip freeze > requirements.txt
```

## 4. 撰寫 Chirp 程式碼

Chirp 主要提供兩種用法：

1. [Synchronous speech recognition](https://cloud.google.com/speech-to-text/v2/docs/sync-recognize)

    適用於**短音頻**片段 (最多 `60` 秒的音頻)，可立即返回轉錄結果。

    同步語音辨識可以轉錄**本機上傳的 WAV 檔案**或是儲存在 **Cloud Storage** 的音訊。

    > 注意: 提供超過 `60s` 或 `10MB` 的音頻會導致 API 返回錯誤，詳見 [quotas and limits](https://cloud.google.com/speech-to-text/v2/quotas) 說明。

2. [Batch speech recognition](https://cloud.google.com/speech-to-text/v2/docs/batch-recognize)

    適用於**長音頻**片段 (超過 `60` 秒的音頻)，以透過非同步方式進行轉錄，但非同步語音辨識的上限 為 480 分鐘 (即 8 小時)。

    批次語音辨識僅能轉錄儲存在 **Cloud Storage** 的音訊。

以下我直接列出一段完整的 Python 原始碼，示範「同步語音辨識」的轉錄方法，原始碼放入 `main.py` 檔案就可以執行：

```python
import os

from google.api_core.client_options import ClientOptions
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech

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
```

執行 `main.py` 程式碼：

```bash
python main.py
```

你應該會看到類似以下的輸出：

```bash
步驟 1: 偵測音訊檔案的語言...
Transcript:  开 启 流 览 器
Detected Language: zh-Hans
偵測到的語言: zh-Hans

步驟 2: 使用指定的語言 en-US 進行精確轉錄...
Transcript:  open google chrome

步驟 3: 使用指定的語言 cmn-Hant-TW 進行精確轉錄...
Transcript:  開啟流器

轉錄完成!
```

## 5. 結語

這篇文章我們介紹了 Google Cloud 的 Chirp 通用語音模型，並示範了如何使用 Python 語言進行語音轉文字。

我自己實測的結果，發現「英文」的識別率非常高，而「中文」的識別率則相對較低，且叫無法區分不同地區的口音。你應該可以從結果發現，該模型雖然宣稱 Universal speech model (USM) (通用語音模型) 可以處理多種語言，但在實際應用中，還是對於台灣這邊的口音，辨識率依然不高，會自動辨識為簡體中文(`zh-Hans`)。另外一個問題是，台灣人講話很喜歡用晶晶體說話，也就是很喜歡夾雜著中、英文混著說，而這種語音在 Chirp 的辨識率依然非常低，大部分時候會直接濾掉英文的部分。

不過，Google 對 USM 野心很大，目前他們已經用了 1,200 萬小時的語音檔進行自監督訓練，在一百多種語言微調了 280 億個句子，訓練出了一個 `2B` 參數的模型。其實 `2B` 其實蠻小的，要處理這麼多的語言，我覺得還是相當困難。這個 Chirp 模型雖然可以處理多種語言的語音，但在實際應用中，還是有很多問題需要解決，尤其是多語言的語音辨識部分，期待未來 Google 的語音技術可以解決這些問題，希望有一天可以不用再打字了！😄

### 相關連結

- [Package google.cloud.speech.v2 | Cloud Speech-to-Text V2 documentation | Google Cloud](https://cloud.google.com/speech-to-text/v2/docs/reference/rpc/google.cloud.speech.v2#google.cloud.speech.v2.Speech.BatchRecognize)
- [Speech-to-Text API 定價 | Google Cloud](https://cloud.google.com/speech-to-text/pricing?hl=zh_tw)
- [Perfect voice applications with Chirp and speech fine tuning - YouTube](https://www.youtube.com/watch?v=xT348FrrFZ0)
