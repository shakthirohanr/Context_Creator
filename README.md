# Context Creator

Context Creator is a Python application designed to help users generate or manage contextual information for their projects or data analysis tasks. It streamlines the process of creating and organizing context, making it easier to understand and utilize data effectively.

## Installation Instructions

To get started with Context Creator, you'll need to install its dependencies.

1.  **Ensure Python is installed:** Make sure you have Python 3.6 or newer installed on your system. You can download it from [python.org](https://www.python.org/downloads/).
2.  **Clone the repository (if applicable):**
    ```bash
    git clone <your-repository-url>
    cd <repository-name>
    ```
3.  **Install dependencies:**
    This project uses a `requirements.txt` file to manage its dependencies. Open your terminal or command prompt and run the following command in the project's root directory:
    ```bash
    pip install -r requirements.txt
    ```
    This will install all the necessary libraries.

## Usage Instructions

To run Context Creator, navigate to the project's root directory in your terminal or command prompt and execute the main script:

```bash
python contextCreator.py
```

Follow any on-screen prompts or instructions provided by the application.

## Build Instructions with PyInstaller

You can package Context Creator into a standalone executable using PyInstaller. This allows you to run the application on systems without Python installed.

1.  **Install PyInstaller:**
    If you don't have PyInstaller installed, open your terminal or command prompt and run:
    ```bash
    pip install pyinstaller
    ```

2.  **Build the Executable:**
    Navigate to the project's root directory in your terminal.

    *   **For a single-file executable (recommended for simplicity):**
        This bundles everything into one `.exe` file.
        ```bash
        pyinstaller --onefile contextCreator.py
        ```

    *   **For a one-folder bundle:**
        This creates a folder with the executable and all its dependencies.
        ```bash
        pyinstaller --onedir contextCreator.py
        ```

    *   **Optional Flags:**
        *   **`--noconsole`**: (For GUI applications) Prevents the command prompt window from appearing when you run the executable.
            ```bash
            pyinstaller --onefile --noconsole contextCreator.py
            ```
        *   **`--icon=<path/to/your/icon.ico>`**: (Windows) or `<path/to/your/icon.icns>` (macOS) Adds a custom icon to your executable. Replace `youricon.ico` with the actual path to your icon file.
            ```bash
            pyinstaller --onefile --noconsole --icon=assets/icon.ico contextCreator.py
            ```
        *   **`--name <YourAppName>`**: You can specify a name for your executable and build artifacts.
            ```bash
            pyinstaller --onefile --name ContextCreatorApp contextCreator.py
            ```

3.  **Output Location:**
    PyInstaller will create a few folders in your project's root directory:
    *   `build`: Contains temporary build files.
    *   `dist`: This is where your executable or distribution folder is located.
        *   If you used `--onefile`, you'll find `contextCreator.exe` (or `contextCreator` on macOS/Linux) inside `dist`.
        *   If you used `--onedir`, you'll find a folder named `contextCreator` inside `dist`, containing the executable and its dependencies.

    You can distribute the contents of the `dist` folder.

---

Happy context creating!
