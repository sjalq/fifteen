use image::{ImageBuffer, Rgba, RgbaImage};

/// Generate the blue/white icon as raw RGBA bytes
pub fn generate_icon_rgba() -> RgbaImage {
    // Create a 32x32 blue image with white square
    ImageBuffer::from_fn(32, 32, |x, y| {
        // Blue background (RGB: 0, 120, 215)
        let mut color = Rgba([0u8, 120u8, 215u8, 255u8]);

        // White square in center (10x10 pixels)
        if x >= 11 && x <= 20 && y >= 11 && y <= 20 {
            color = Rgba([255u8, 255u8, 255u8, 255u8]);
        }

        color
    })
}

/// Generate icon as RGBA bytes for tray icon
pub fn generate_icon_png() -> Vec<u8> {
    let img = generate_icon_rgba();
    img.into_raw()
}

/// Generate multiple icon sizes for Windows
pub fn generate_icon_sizes() -> Vec<(u32, RgbaImage)> {
    let sizes = vec![16, 32, 48, 64, 128, 256];
    sizes.into_iter().map(|size| {
        let img = ImageBuffer::from_fn(size, size, |x, y| {
            // Scale the design proportionally
            let scale = size as f32 / 32.0;
            let center_start = (11.0 * scale) as u32;
            let center_end = (20.0 * scale) as u32;

            // Blue background (RGB: 0, 120, 215)
            let mut color = Rgba([0u8, 120u8, 215u8, 255u8]);

            // White square in center
            if x >= center_start && x <= center_end && y >= center_start && y <= center_end {
                color = Rgba([255u8, 255u8, 255u8, 255u8]);
            }

            color
        });
        (size, img)
    }).collect()
}