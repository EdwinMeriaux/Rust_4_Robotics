use image::GrayImage;
use imageproc::contrast::threshold;
use rayon::prelude::*;
use rayon::ThreadPoolBuilder;
use serde_json::json;
use std::collections::HashMap;
use std::env;
use std::fs::{self, File};
use std::io::Write;
use std::path::Path;
use std::process;
use std::time::Instant;

fn bresenham_line(x0: i32, y0: i32, x1: i32, y1: i32) -> Vec<(i32, i32)> {
    let mut points = Vec::new();
    let (mut x, mut y) = (x0, y0);
    let dx = (x1 - x).abs();
    let dy = (y1 - y).abs();
    let sx = if x < x1 { 1 } else { -1 };
    let sy = if y < y1 { 1 } else { -1 };
    let mut err = dx - dy;

    loop {
        points.push((x, y));
        if x == x1 && y == y1 {
            break;
        }
        let e2 = err * 2;
        if e2 > -dy {
            err -= dy;
            x += sx;
        }
        if e2 < dx {
            err += dx;
            y += sy;
        }
    }
    points
}

fn is_line_clear(p1: (i32, i32), p2: (i32, i32), img: &GrayImage) -> bool {
    for &(x, y) in &bresenham_line(p1.0, p1.1, p2.0, p2.1) {
        if img.get_pixel(x as u32, y as u32)[0] == 0 {
            return false;
        }
    }
    true
}

/// Parses arguments:
///   WIDTHxHEIGHT   (e.g. "1920x1080")
///   input.png      (image path)
///   output.json    (output path)
///   [THREAD_COUNT] (optional number of rayon threads)
fn parse_input(args: Vec<String>) -> (u32, u32, String, String, usize) {
    let mut width = 5000;
    let mut height = 5000;
    let mut img_path = String::new();
    let mut json_path = String::new();
    let mut threads = std::thread::available_parallelism()
        .map(|n| n.get())
        .unwrap_or(1);

    for arg in args.into_iter().skip(1) {
        if arg.contains('x') {
            let parts: Vec<&str> = arg.split('x').collect();
            if parts.len() == 2 {
                if let (Ok(w), Ok(h)) = (parts[0].parse(), parts[1].parse()) {
                    width = w;
                    height = h;
                }
            }
        } else if arg.ends_with(".png") {
            img_path = arg;
        } else if arg.ends_with(".json") {
            json_path = arg;
        } else if let Ok(n) = arg.parse::<usize>() {
            threads = n;
        }
    }

    (width, height, img_path, json_path, threads)
}

fn main() {
    let start = Instant::now();
    let args: Vec<String> = env::args().collect();
    let (width, height, img_path, json_path, threads) = parse_input(args);

    // check image file exists
    if !Path::new(&img_path).exists() {
        eprintln!("Error: Image file '{}' not found. Please check the path.", img_path);
        process::exit(1);
    }

    // build rayon thread pool
    ThreadPoolBuilder::new()
        .num_threads(threads)
        .build_global()
        .expect("Failed to configure rayon thread pool");

    // load & preprocess image
    let img = image::open(&img_path).unwrap_or_else(|e| {
        eprintln!("Error loading image '{}': {}", img_path, e);
        process::exit(1);
    });
    let gray = img.to_luma8();
    let resized = image::imageops::resize(
        &gray,
        width,
        height,
        image::imageops::FilterType::Triangle,
    );
    let binary = threshold(&resized, 128);

    // collect points
    let mut white = Vec::new();
    let mut black = Vec::new();
    let mut all = Vec::new();
    for y in 0..binary.height() {
        for x in 0..binary.width() {
            let p = (x as i32, y as i32);
            all.push(p);
            if binary.get_pixel(x, y)[0] == 255 {
                white.push(p);
            } else {
                black.push(p);
            }
        }
    }

    // compute visibility
    let visibility: HashMap<(i32, i32), Vec<(i32, i32)>> = all
        .par_iter()
        .map(|&p1| {
            let vis = white
                .par_iter()
                .filter_map(|&p2| if p1 == p2 || is_line_clear(p1, p2, &binary) { Some(p2) } else { None })
                .collect();
            (p1, vis)
        })
        .collect();

    // prepare JSON output
    let mut out: HashMap<String, Vec<(i32, i32)>> = visibility
        .into_iter()
        .map(|((x, y), pts)| (format!("({}, {})", x, y), pts))
        .collect();
    out.insert("blocked".to_string(), black);
    out.insert("all".to_string(), all);

    // write JSON file
    let data = json!(out).to_string();
    let mut file = File::create(&json_path).unwrap_or_else(|e| {
        eprintln!("Error creating JSON '{}': {}", json_path, e);
        process::exit(1);
    });
    file.write_all(data.as_bytes()).unwrap_or_else(|e| {
        eprintln!("Error writing JSON '{}': {}", json_path, e);
        process::exit(1);
    });

    println!("Saved visibility data to '{}'", json_path);
    println!("Total runtime: {:.4} s", start.elapsed().as_secs_f64());
}
