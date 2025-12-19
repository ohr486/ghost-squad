FROM golang:1.25-alpine

WORKDIR /app

# 先にすべてのファイルをコピーします
# (main.go がないと go mod tidy が依存関係を正しく認識できないため)
COPY . .

# 依存関係の整理とダウンロード
RUN go mod tidy

# ビルド
RUN go build -o gs main.go

CMD ["./gs"]
