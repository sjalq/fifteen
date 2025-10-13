use std::env;
use std::path::Path;

fn main() {
    // Only embed resources on Windows
    if cfg!(windows) {
        let manifest_dir = env::var("CARGO_MANIFEST_DIR").unwrap();
        let icon_path = Path::new(&manifest_dir).join("icon.ico");

        // Generate icon if it doesn't exist
        if !icon_path.exists() {
            generate_icon(&icon_path);
        }

        // Set up Windows resources
        let mut res = winres::WindowsResource::new();
        res.set_icon(icon_path.to_str().unwrap());
        res.compile().unwrap();
    }
}

fn generate_icon(path: &Path) {
    use image::{ImageBuffer, Rgba};
    use std::fs::File;
    use std::io::Write;

    // Create a 32x32 blue image with white square
    let img = ImageBuffer::from_fn(32, 32, |x, y| {
        // Blue background (RGB: 0, 120, 215)
        let mut color = Rgba([0u8, 120u8, 215u8, 255u8]);

        // White square in center (10x10 pixels)
        if x >= 11 && x <= 20 && y >= 11 && y <= 20 {
            color = Rgba([255u8, 255u8, 255u8, 255u8]);
        }

        color
    });

    // Save as PNG first
    let png_path = path.with_extension("png");
    img.save(&png_path).unwrap();

    // Convert PNG to ICO format
    // For simplicity, we'll create a basic ICO with one 32x32 image
    let png_data = std::fs::read(&png_path).unwrap();

    let mut ico_data = Vec::new();

    // ICO header
    ico_data.extend_from_slice(&[0, 0]); // Reserved
    ico_data.extend_from_slice(&[1, 0]); // Type (1 = ICO)
    ico_data.extend_from_slice(&[1, 0]); // Number of images

    // Image directory entry
    ico_data.push(32); // Width
    ico_data.push(32); // Height
    ico_data.push(0);  // Color palette
    ico_data.push(0);  // Reserved
    ico_data.extend_from_slice(&[1, 0]); // Color planes
    ico_data.extend_from_slice(&[32, 0]); // Bits per pixel

    let size = png_data.len() as u32;
    ico_data.extend_from_slice(&size.to_le_bytes()); // Image size
    ico_data.extend_from_slice(&[22, 0, 0, 0]); // Offset to image data

    // Append PNG data
    ico_data.extend_from_slice(&png_data);

    // Write ICO file
    let mut file = File::create(path).unwrap();
    file.write_all(&ico_data).unwrap();

    // Clean up temporary PNG
    std::fs::remove_file(png_path).ok();
}