#include <windows.h>
#include <wchar.h>

static void parent_directory(wchar_t *path) {
    wchar_t *slash = wcsrchr(path, L'\\');
    if (slash) *slash = L'\0';
}

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE previous, PWSTR arguments, int show) {
    (void)instance;
    (void)previous;
    (void)show;

    wchar_t launcher[MAX_PATH];
    if (!GetModuleFileNameW(NULL, launcher, MAX_PATH)) return 2;

    wchar_t directory[MAX_PATH];
    wcsncpy(directory, launcher, MAX_PATH - 1);
    directory[MAX_PATH - 1] = L'\0';
    parent_directory(directory);

    wchar_t runtime[MAX_PATH];
    wchar_t script[MAX_PATH];
    _snwprintf(runtime, MAX_PATH, L"%ls\\CUKTECHRuntime.exe", directory);
    _snwprintf(script, MAX_PATH, L"%ls\\app\\windows\\AP01ScreenController.py", directory);
    runtime[MAX_PATH - 1] = L'\0';
    script[MAX_PATH - 1] = L'\0';

    DWORD required = (DWORD)(wcslen(runtime) + wcslen(script) + wcslen(arguments) + 16);
    wchar_t *command = (wchar_t *)LocalAlloc(LPTR, required * sizeof(wchar_t));
    if (!command) return 3;
    _snwprintf(command, required, L"\"%ls\" \"%ls\" %ls", runtime, script, arguments);
    command[required - 1] = L'\0';

    SetEnvironmentVariableW(L"CUKTECH_LAUNCHER_EXE", launcher);
    STARTUPINFOW startup;
    PROCESS_INFORMATION process;
    ZeroMemory(&startup, sizeof(startup));
    ZeroMemory(&process, sizeof(process));
    startup.cb = sizeof(startup);

    BOOL created = CreateProcessW(
        runtime,
        command,
        NULL,
        NULL,
        FALSE,
        CREATE_UNICODE_ENVIRONMENT,
        NULL,
        directory,
        &startup,
        &process
    );
    if (!created) {
        DWORD error = GetLastError();
        wchar_t message[512];
        _snwprintf(
            message,
            512,
            L"CUKTECH Screen Controller could not start.\n\nWindows error: %lu",
            error
        );
        MessageBoxW(NULL, message, L"CUKTECH Screen Controller", MB_OK | MB_ICONERROR);
        LocalFree(command);
        return (int)error;
    }

    CloseHandle(process.hThread);
    CloseHandle(process.hProcess);
    LocalFree(command);
    return 0;
}
