MinTTY is the terminal emulator that comes by default with Git
for Windows. It has known issues with gh's ability to prompt a
user for input.

There are a few workarounds to make gh work with MinTTY:

- Reinstall Git for Windows, checking "Enable experimental support for pseudo consoles".

- Use a different terminal emulator with Git for Windows like Windows Terminal.
  You can run `C:\Program Files\Git\bin\bash.exe` from any terminal emulator to continue
  using all of the tooling in Git For Windows without MinTTY.

- Prefix invocations of gh with `winpty`, eg: `winpty gh auth login`.
  NOTE: this can lead to some UI bugs.
