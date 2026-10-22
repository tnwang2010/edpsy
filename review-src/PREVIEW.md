# PR 分支預覽

課後複習使用 raw.githack 的靜態檔案託管，以完整 commit SHA 固定預覽版本。
這個服務直接提供 GitHub 分支上的 HTML、CSS 與圖片，不需要另外開設帳號；正式站仍由 GitHub Pages 發布。
服務說明：https://raw.githack.com/

## 發布預覽與建立 PR

1. 從最新的 `main` 建立修改分支，修改 `review-src/`。
2. 在儲存庫根目錄執行 `python3 review-src/tools/build.py`。
3. 將來源與 `review/` 產出一起 commit，推送修改分支至 GitHub。
4. 執行 `python3 review-src/tools/preview.py 完整的_commit_SHA`。其他週次可加上 `--page review/week01/index.html --section s1`。
5. 程式會載入該版本的頁面，以及所有站內連結所需的 HTML、樣式和圖片，逐檔比對本機產出；只有全部相同才會輸出成功訊息與預覽連結。
6. 在瀏覽器確認頁面，將預覽連結放在 PR 說明開頭，再建立 PR。每次修改後須以新 commit 重做第 4、5 步並更新連結。

瀏覽器第一次進入時，raw.githack 可能顯示目的網址確認頁。確認後即可閱讀同一儲存庫的預覽。
產生器使用明確的 `index.html` 連結，讓首頁與跨週導覽也能在靜態檔案託管上運作。
