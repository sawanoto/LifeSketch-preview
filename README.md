# LifeSketch PR previews

公開中の `sawanoto/LifeSketch` を変更せず、同じリポジトリ内の未マージPRを別のGitHub Pagesサイトへ配信します。

- 一覧: https://sawanoto.github.io/LifeSketch-preview/
- PRごとのURL: `https://sawanoto.github.io/LifeSketch-preview/pr-N/`
- PR #1: https://sawanoto.github.io/LifeSketch-preview/pr-1/001_doremi-pipes/

## 更新

GitHub Actionsの `Refresh PR previews` が約5分間隔でPRのコミットを比較し、変更があると配信します。GitHubのスケジュール実行は混雑で遅延することがあります。急ぐ場合は Actions → Refresh PR previews → Run workflow で更新できます。PRを閉じると次の更新でプレビューを外します。60日間このリポジトリに更新がないとGitHubが定期実行を停止する場合があるため、Actionsで再有効化してください。

`manifest.json` と各 `pr-N/preview-info.json` に反映済みコミットを記録します。スマートフォンで古い表示が残る場合はページを再読み込みしてください。

## 方式の比較

|方式|管理と既存サイトへの影響|
|---|---|
|本番Pages内にPRフォルダーを置く|本番の公開元・配信処理を変更する必要がある|
|Netlify / Cloudflare Pages等|更新イベントで配信できるが、追加サービスへの接続と管理が必要|
|専用リポジトリのGitHub Pages（採用）|GitHubだけで管理でき、本番の公開元を変更しない。定期確認の反映待ちがある|

PRのファイルは静的データとしてコピーします。PR内のスクリプトやワークフローをサーバー側で実行しません。別リポジトリの書き込みトークンや追加の秘密情報は使いません。forkからのPRは自動配信対象外です。

このサイトは公開の確認用環境です。p5.js・p5.soundは作品が指定するCDNからブラウザーへ読み込まれます。PCとスマートフォンの双方でパイプや音名ボタンを押し、音の高さ、タップ、画面幅を確認してください。
