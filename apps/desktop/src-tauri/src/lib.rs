use std::net::TcpStream;
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::time::Duration;

use serde::Serialize;
use tauri::Manager;

struct ApiState {
    child: Mutex<Option<Child>>,
}

#[tauri::command]
fn greet(name: &str) -> String {
    format!(
        "Hello, {}! Welcome to MetaAgent Studio (Tauri v2 + React).",
        name
    )
}

fn api_dir() -> PathBuf {
    if let Ok(p) = std::env::var("METAAGENT_API_DIR") {
        return PathBuf::from(p);
    }
    // Dev: repo apps/api relative to cwd or common layouts
    let candidates = [
        PathBuf::from("../api"),
        PathBuf::from("../../api"),
        PathBuf::from("apps/api"),
        PathBuf::from("/workspace/apps/api"),
    ];
    for c in candidates {
        if c.join("app").join("main.py").exists() {
            return c;
        }
    }
    PathBuf::from("/workspace/apps/api")
}

fn data_dir() -> PathBuf {
    if let Ok(p) = std::env::var("METAAGENT_DB_PATH") {
        return PathBuf::from(p);
    }
    let home = std::env::var("HOME").unwrap_or_else(|_| "/tmp".into());
    PathBuf::from(home)
        .join(".metaagent")
        .join("studio-demo.db")
}

fn port_open(host: &str, port: u16) -> bool {
    TcpStream::connect_timeout(
        &format!("{host}:{port}").parse().unwrap(),
        Duration::from_millis(300),
    )
    .is_ok()
}

#[derive(Serialize)]
struct StatusOut {
    running: bool,
    detail: String,
}

#[tauri::command]
fn api_status() -> StatusOut {
    if port_open("127.0.0.1", 8000) {
        StatusOut {
            running: true,
            detail: "API port 8000 is open".into(),
        }
    } else {
        StatusOut {
            running: false,
            detail: "API not listening".into(),
        }
    }
}

#[tauri::command]
fn ollama_status() -> StatusOut {
    if port_open("127.0.0.1", 11434) {
        StatusOut {
            running: true,
            detail: "Ollama port 11434 is open".into(),
        }
    } else {
        StatusOut {
            running: false,
            detail: "Ollama not listening".into(),
        }
    }
}

#[tauri::command]
fn start_api(state: tauri::State<'_, ApiState>) -> Result<StatusOut, String> {
    if port_open("127.0.0.1", 8000) {
        return Ok(StatusOut {
            running: true,
            detail: "API already running".into(),
        });
    }

    let dir = api_dir();
    if !dir.join("app").join("main.py").exists() {
        return Err(format!("API not found at {}", dir.display()));
    }

    let venv_python = dir.join(".venv/bin/python");
    let python = if venv_python.exists() {
        venv_python
    } else {
        PathBuf::from("python3")
    };

    let db = data_dir();
    if let Some(parent) = db.parent() {
        let _ = std::fs::create_dir_all(parent);
    }

    let mut cmd = Command::new(&python);
    cmd.current_dir(&dir)
        .arg("-m")
        .arg("uvicorn")
        .arg("app.main:app")
        .arg("--host")
        .arg("127.0.0.1")
        .arg("--port")
        .arg("8000")
        .env("METAAGENT_LLM_MODE", "live")
        .env("METAAGENT_DEMO_UNLOCK", "1")
        .env("METAAGENT_DB_PATH", &db)
        .stdout(Stdio::null())
        .stderr(Stdio::null());

    let child = cmd
        .spawn()
        .map_err(|e| format!("Failed to start API with {}: {e}", python.display()))?;

    {
        let mut guard = state.child.lock().map_err(|e| e.to_string())?;
        *guard = Some(child);
    }

    // Wait briefly for bind
    for _ in 0..40 {
        if port_open("127.0.0.1", 8000) {
            return Ok(StatusOut {
                running: true,
                detail: "API started".into(),
            });
        }
        std::thread::sleep(Duration::from_millis(250));
    }

    Err("API process started but port 8000 never opened".into())
}

#[tauri::command]
fn stop_api(state: tauri::State<'_, ApiState>) -> Result<StatusOut, String> {
    let mut guard = state.child.lock().map_err(|e| e.to_string())?;
    if let Some(mut child) = guard.take() {
        let _ = child.kill();
        let _ = child.wait();
    }
    Ok(StatusOut {
        running: false,
        detail: "API stop requested".into(),
    })
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .manage(ApiState {
            child: Mutex::new(None),
        })
        .setup(|app| {
            let handle = app.handle().clone();
            std::thread::spawn(move || {
                let state = handle.state::<ApiState>();
                let _ = start_api(state);
            });
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            greet,
            start_api,
            stop_api,
            api_status,
            ollama_status
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
