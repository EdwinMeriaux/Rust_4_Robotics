use image::{DynamicImage, GenericImageView, Luma, GrayImage};
use imageproc::contrast::threshold;
use rayon::prelude::*;
use serde_json::json;
use std::collections::HashMap;
use std::env;
use std::fs::File;
use std::io::Write;
use std::time::Instant;

fn bresenham_line(x0: i32, y0: i32, x1: i32, y1: i32) -> Vec<(i32, i32)> {
    let mut points = Vec::new();
    let mut x0 = x0;
    let mut y0 = y0;
    let dx = (x1 - x0).abs();
    let dy = (y1 - y0).abs();
    let sx = if x0 < x1 { 1 } else { -1 };
    let sy = if y0 < y1 { 1 } else { -1 };
    let mut err = dx - dy;

    loop {
        points.push((x0, y0));
        if x0 == x1 && y0 == y1 {
            break;
        }
        let e2 = err * 2;
        if e2 > -dy {
            err -= dy;
            x0 += sx;
        }
        if e2 < dx {
            err += dx;
            y0 += sy;
        }
    }
    points
}

fn is_line_clear(p1: (i32, i32), p2: (i32, i32), binary_image: &GrayImage) -> bool {
    let line_points = bresenham_line(p1.0, p1.1, p2.0, p2.1);
    for &(x, y) in &line_points {
        if binary_image.get_pixel(x as u32, y as u32)[0] == 0 {
            return false;
        }
    }
    true
}

fn parse_points(args: Vec<String>) -> (Vec<(i32, i32)>, u32, u32, String, String) {
    let mut points = Vec::new();
    let mut width = 5000; // Default width
    let mut height = 5000; // Default height
    let mut image_path = String::new(); // To store the image path
    let mut json_file = String::new(); // To store the JSON file name

    for arg in args.iter().skip(1) {
        if arg.starts_with("(") && arg.contains(",") {
            let parts: Vec<&str> = arg.trim_matches(|c| c == '(' || c == ')' || c == ' ')
                .split(',')
                .collect();
            if parts.len() == 2 {
                if let (Ok(x), Ok(y)) = (parts[0].parse::<i32>(), parts[1].parse::<i32>()) {
                    points.push((x, y));
                }
            }
        } else if arg.contains("x") {
            let dimensions: Vec<&str> = arg.split('x').collect();
            if dimensions.len() == 2 {
                if let (Ok(w), Ok(h)) = (dimensions[0].parse::<u32>(), dimensions[1].parse::<u32>()) {
                    width = w;
                    height = h;
                }
            }
        } else if arg.ends_with(".png") {
            image_path = arg.clone(); // Store the PNG image path
        } else if arg.ends_with(".json") {
            json_file = arg.clone(); // Store the JSON file name
        }
    }
    (points, width, height, image_path, json_file)
}

fn main() {
    let start_time = Instant::now();
    let args: Vec<String> = env::args().collect();
    let (points_to_check, width, height, image_path, json_file) = parse_points(args);

    let img = image::open(&image_path).expect("Failed to load image");

    let grayscale_image = img.to_luma8();
    let resized_image = image::imageops::resize(&grayscale_image, width, height, image::imageops::FilterType::Triangle);
    let binary_image = threshold(&resized_image, 128);

    let mut white_points = Vec::new();
    let mut black_points = Vec::new();
    let mut all_points = Vec::new();

    for y in 0..binary_image.height() {
        for x in 0..binary_image.width() {
            all_points.push((x as i32, y as i32));
            if binary_image.get_pixel(x, y)[0] == 255 {
                white_points.push((x as i32, y as i32));
            } else {
                black_points.push((x as i32, y as i32));
            }
        }
    }

    let visibility_dict: HashMap<(i32, i32), Vec<(i32, i32)>> = points_to_check
        .par_iter()
        .map(|&point1| {
            let visible_points: Vec<(i32, i32)> = white_points
                .par_iter()
                .filter_map(|&point2| {
                    if point1 == point2 || is_line_clear(point1, point2, &binary_image) {
                        Some(point2)
                    } else {
                        None
                    }
                })
                .collect();
            (point1, visible_points)
        })
        .collect();

    // Create JSON dictionary with "blocked" and "all" entries, storing points as arrays of numbers
    let mut json_dict: HashMap<String, Vec<(i32, i32)>> = visibility_dict
        .into_iter()
        .map(|((x1, y1), points)| {
            let point_tuple = (x1, y1); // Use tuple for the current point
            let visible_points_vec: Vec<(i32, i32)> = points
                .into_iter()
                .map(|(x2, y2)| (x2, y2)) // Use tuple for each visible point
                .collect();
            (format!("({}, {})", x1, y1), visible_points_vec) // Create the entry
        })
        .collect();

    // Insert the "blocked" and "all" entries after the initial collection
    json_dict.insert("blocked".to_string(), black_points
        .into_iter()
        .map(|(x, y)| (x, y)) // Use tuple for each black point
        .collect());

    json_dict.insert("all".to_string(), all_points
        .into_iter()
        .map(|(x, y)| (x, y)) // Use tuple for each point in all_points
        .collect());


    let json_data = json!(json_dict).to_string();
    let mut file = File::create(&json_file).expect("Unable to create file");
    file.write_all(json_data.as_bytes()).expect("Unable to write data");
    println!("Saved visibility data to '{}'", json_file);
    println!("Total runtime: {:.4} seconds", start_time.elapsed().as_secs_f64());
}
