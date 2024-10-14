# Web App Name: Image Cropper Pro

## User Requirements
Create a web application that allows users to crop images using a movable rectangle that indicates the cropping area. Users should be able to zoom in and out using buttons or the mouse wheel, and pan the image by moving the cropping rectangle. The previewed image must be contained within a scrollable area to prevent overflow.

## Libraries to Use
- **HTML5 Canvas**: For rendering and manipulating images.
- **Cropper.js**: A JavaScript library for cropping images with a user-friendly interface.
- **jQuery**: For DOM manipulation and event handling.

## User Interface Plan
### Layout
- **Header**: 
  - Title: "Image Cropper Pro"
  - Upload Button: To select an image file from the device.
  
- **Main Area**:
  - **Image Container**: A div with overflow properties to contain the image and cropping rectangle.
    - **Image Display Area**: A canvas element to display the uploaded image.
    - **Movable Cropping Rectangle**: A visual rectangle that indicates the cropping area.
  
- **Controls**:
  - **Zoom Controls**:
    - Zoom In Button: To increase the zoom level.
    - Zoom Out Button: To decrease the zoom level.
    - Mouse Wheel Support: To zoom in and out using the mouse wheel.
  - **Pan Controls**: 
    - Arrow buttons to pan the image within the cropping area.
  
- **Footer**:
  - Crop Button: To finalize the cropping action.
  - Reset Button: To reset the image to its original state.
  - Download Button: To download the cropped image.

## Use Cases
1. **Upload Image**: 
   - User clicks the upload button and selects an image file.
   - The image is displayed in the image container.

2. **Adjust Cropping Rectangle**:
   - User can drag the cropping rectangle to reposition it.
   - The cropping rectangle can be resized by dragging its corners.

3. **Zoom Image**:
   - User clicks the zoom in/out buttons to adjust the zoom level.
   - User can also use the mouse wheel to zoom in and out.

4. **Pan Image**:
   - User clicks the arrow buttons to pan the image within the cropping area.
   - The cropping rectangle moves accordingly.

5. **Crop Image**:
   - User clicks the crop button.
   - The application processes the image and displays the cropped version.

6. **Reset Image**:
   - User clicks the reset button.
   - The image returns to its original state.

7. **Download Cropped Image**:
   - User clicks the download button.
   - The cropped image is saved to the user's device.

## Code Structure
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Image Cropper Pro</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.15/cropper.min.css" />
    <style>
        body {
            background: linear-gradient(to right, #e0f7fa, #fce4ec);
        }
        #imageContainer {
            width: 100%;
            height: 400px;
            overflow: auto;
            position: relative;
            border: 1px solid #ccc;
        }
        #imageCanvas {
            display: none;
        }
        .cropper-rectangle {
            border: 2px dashed #ff0000;
            position: absolute;
            cursor: move;
        }
    </style>
</head>
<body>
    <header>
        <h1>Image Cropper Pro</h1>
        <input type="file" id="upload" accept="image/*">
    </header>
    <main>
        <div id="imageContainer">
            <canvas id="imageCanvas"></canvas>
            <img id="image" class="hidden">
            <div class="cropper-rectangle" id="cropperRectangle"></div>
        </div>
        <div id="controls">
            <button id="zoomIn">Zoom In</button>
            <button id="zoomOut">Zoom Out</button>
        </div>
    </main>
    <footer>
        <button id="crop">Crop</button>
        <button id="reset">Reset</button>
        <button id="download">Download</button>
    </footer>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.15/cropper.min.js"></script>
    <script>
        const upload = document.getElementById('upload');
        const imageCanvas = document.getElementById('imageCanvas');
        const image = document.getElementById('image');
        const cropperRectangle = document.getElementById('cropperRectangle');
        let cropper;

        upload.addEventListener('change', (event) => {
            const file = event.target.files[0];
            const reader = new FileReader();
            reader.onload = (e) => {
                image.src = e.target.result;
                image.onload = () => {
                    imageCanvas.style.display = 'block';
                    cropper = new Cropper(image, {
                        aspectRatio: 1,
                        viewMode: 1,
                        autoCropArea: 1,
                        crop: (event) => {
                            cropperRectangle.style.width = event.detail.width + 'px';
                            cropperRectangle.style.height = event.detail.height + 'px';
                            cropperRectangle.style.left = event.detail.x + 'px';
                            cropperRectangle.style.top = event.detail.y + 'px';
                        }
                    });
                };
            };
            reader.readAsDataURL(file);
        });

        document.getElementById('zoomIn').addEventListener('click', () => {
            cropper.zoom(0.1);
        });

        document.getElementById('zoomOut').addEventListener('click', () => {
            cropper.zoom(-0.1);
        });

        document.getElementById('crop').addEventListener('click', () => {
            const canvas = cropper.getCroppedCanvas();
            const croppedImage = canvas.toDataURL();
            const link = document.createElement('a');
            link.href = croppedImage;
            link.download = 'cropped-image.png';
            link.click();
        });

        document.getElementById('reset').addEventListener('click', () => {
            cropper.reset();
        });

        document.getElementById('download').addEventListener('click', () => {
            const canvas = cropper.getCroppedCanvas();
            const croppedImage = canvas.toDataURL();
            const link = document.createElement('a');
            link.href = croppedImage;
            link.download = 'cropped-image.png';
            link.click();
        });

        // Mouse wheel zoom
        imageContainer.addEventListener('wheel', (event) => {
            event.preventDefault();
            if (event.deltaY < 0) {
                cropper.zoom(0.1);
            } else {
                cropper.zoom(-0.1);
            }
        });
    </script>
</body>
</html>
```