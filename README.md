# lawhub-tool
lawhubプロジェクト用のスクリプトを管理するレポジトリ

## 議案処理用スクリプト
改正法案は以下のように処理されます。

1. 法案に含まれる改正文を、lawhub.Actionクラスにそれぞれ変換し、JSON Lines形式で保存する（[parse_gian.py](parse_gian.py)）
2. 改正対象の法律のxmlファイルをlawhub-xmlレポジトリから取得する（[copy_law.py](copy_law.py)）
3. パースしたActionを対象のxmlファイルに適用し、TEXT形式で保存する（[apply_gian.py](apply_gian.py)）
4. 処理結果に基づき、lawhubレポジトリにpull requestを作成する（[create_pull_request.py](create_pull_request.py)）

[pipeline.py](pipeline.py)を使ってこれらのタスクをバッチ処理することができます。


## masterトラック用スクリプト
e-Govデータの更新に伴い、lawhub及びlawhub-xmlレポジトリのmasterブランチを更新します。

* [update_lawhub.py](update_lawhub.py)
* [update_lawhub_xml.py](update_lawhub_xml.py)
