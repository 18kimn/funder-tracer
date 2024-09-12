# Script to turn DTIC search into a spreadsheet

Searches and aggregates data from [https://dtic.dimensions.ai](https://dtic.dimensions.ai).

How to run:

1. Open a terminal
2. Run one of these, depending on your platform (Windows, Linux, or MacOS)

```
curl https://github.com/18kimn/funder-tracer/releases/download/v0.1.0/dtic-macos -o dtic
curl https://github.com/18kimn/funder-tracer/releases/download/v0.1.0/dtic-linux -o dtic
curl https://github.com/18kimn/funder-tracer/releases/download/v0.1.0/dtic-windows.exe  -o dtic-windows.exe
```

3. Update permissions on the downloaded file so that it's executable

```
chmod +x dtic # Or dtic-windows.exe
```

4. Execute the script

```
./dtic
```
