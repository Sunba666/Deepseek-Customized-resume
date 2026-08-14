// Tauri 桌面壳：启动时拉起后端 FastAPI 服务，前端走本地 HTTP。
// 按 ADR-0001，桌面壳在功能全部完成后的最后阶段接入（当前为预留骨架）。
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::{Child, Command};
use std::sync::Mutex;
use tauri::State;

struct Backend(Mutex<Option<Child>>);

fn main() {
    tauri::Builder::default()
        .manage(Backend(Mutex::new(None)))
        .setup(|app| {
            // 启动 Python 后端（需在打包时随附 python 运行时或使用 PyInstaller 产物）
            let child = Command::new("python")
                .args(["backend/run.py"])
                .spawn()
                .ok();
            *app.state::<Backend>().0.lock().unwrap() = child;
            Ok(())
        })
        .on_window_event(|window, event| {
            // 窗口退出时结束后端进程
            if let tauri::WindowEvent::Destroyed = event {
                let app = window.app_handle();
                if let Some(mut child) = app.state::<Backend>().0.lock().unwrap().take() {
                    let _ = child.kill();
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
