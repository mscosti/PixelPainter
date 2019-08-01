const MAX_HEIGHT = 59;

let loadImage = (input) => {
    var input, file, fr, img;

    if (typeof window.FileReader !== 'function') {
        write("The file API isn't supported on this browser yet.");
        return;
    }

    file = input.files[0];
    fr = new FileReader();
    fr.onload = createImage;
    fr.readAsDataURL(file);

    function createImage() {
        var domImage = document.getElementById("domImage");
        img = domImage ? domImage : new Image();
        // img = new Image();
        img.setAttribute("style", "height: 59px !important");
        img.onload = imageLoaded;
        img.src = fr.result;
    }

    function imageLoaded() {
            var canvas = document.getElementById("canvas");
            canvas.width = img.height;
            canvas.height = img.width;
            var ctx = canvas.getContext("2d");
            ctx.imageSmoothingEnabled = false;
            ctx.imageSmoothingQuality = "high"
            ctx.setTransform(
                0,1, // x axis down the screen
               -1,0, // y axis across the screen from right to left
               img.height, // x origin is on the right side of the canvas
               0             // y origin is at the top
           );
            // cx = img.width / 2
            // cy = img.heigh / 2
            // ctx.clearRect(0,0,canvas.width,canvas.height);
            // ctx.save();
            // ctx.translate(cx,cy)
            // ctx.rotate(Math.PI / 2)
            // ctx.translate(-1 * cx, -1 * cy)
            ctx.drawImage(img, 0, 0, img.naturalWidth, img.naturalHeight, 0, 0, img.width, img.height)
            ctx.setTransform(1,0,0,1,0,0)
            // ctx.restore()
            window.fullDataStr = genBitmapImage(ctx.getImageData(0,0,canvas.width, canvas.height))
            canvas.width = img.width;
            canvas.height = img.height;
            ctx.drawImage(img, 0, 0, img.naturalWidth, img.naturalHeight, 0, 0, img.width, img.height)
    }
}

var genBitmapImage = function (oData) {

    var biWidth  = oData.width;
    var biHeight	= oData.height;
    var biSizeImage = biWidth * biHeight * 3;
    var bfSize  = biSizeImage + 54; // total header size = 54 bytes

    console.log("width: " + biWidth);
    console.log("height" + biHeight);

    //
    //  typedef struct tagBITMAPFILEHEADER {
    //  	WORD bfType;
    //  	DWORD bfSize;
    //  	WORD bfReserved1;
    //  	WORD bfReserved2;
    //  	DWORD bfOffBits;
    //  } BITMAPFILEHEADER;
    //
    var BITMAPFILEHEADER = [
        // WORD bfType -- The file type signature; must be "BM"
        0x42, 0x4D,
        // DWORD bfSize -- The size, in bytes, of the bitmap file
        bfSize & 0xff, bfSize >> 8 & 0xff, bfSize >> 16 & 0xff, bfSize >> 24 & 0xff,
        // WORD bfReserved1 -- Reserved; must be zero
        0, 0,
        // WORD bfReserved2 -- Reserved; must be zero
        0, 0,
        // DWORD bfOffBits -- The offset, in bytes, from the beginning of the BITMAPFILEHEADER structure to the bitmap bits.
        54, 0, 0, 0
    ];

    //
    //  typedef struct tagBITMAPINFOHEADER {
    //  	DWORD biSize;
    //  	LONG  biWidth;
    //  	LONG  biHeight;
    //  	WORD  biPlanes;
    //  	WORD  biBitCount;
    //  	DWORD biCompression;
    //  	DWORD biSizeImage;
    //  	LONG  biXPelsPerMeter;
    //  	LONG  biYPelsPerMeter;
    //  	DWORD biClrUsed;
    //  	DWORD biClrImportant;
    //  } BITMAPINFOHEADER, *PBITMAPINFOHEADER;
    //
    var BITMAPINFOHEADER = [
        // DWORD biSize -- The number of bytes required by the structure
        40, 0, 0, 0,
        // LONG biWidth -- The width of the bitmap, in pixels
        biWidth & 0xff, biWidth >> 8 & 0xff, biWidth >> 16 & 0xff, biWidth >> 24 & 0xff,
        // LONG biHeight -- The height of the bitmap, in pixels
        biHeight & 0xff, biHeight >> 8  & 0xff, biHeight >> 16 & 0xff, biHeight >> 24 & 0xff,
        // WORD biPlanes -- The number of planes for the target device. This value must be set to 1
        1, 0,
        // WORD biBitCount -- The number of bits-per-pixel, 24 bits-per-pixel -- the bitmap
        // has a maximum of 2^24 colors (16777216, Truecolor)
        24, 0,
        // DWORD biCompression -- The type of compression, BI_RGB (code 0) -- uncompressed
        0, 0, 0, 0,
        // DWORD biSizeImage -- The size, in bytes, of the image. This may be set to zero for BI_RGB bitmaps
        biSizeImage & 0xff, biSizeImage >> 8 & 0xff, biSizeImage >> 16 & 0xff, biSizeImage >> 24 & 0xff,
        // LONG biXPelsPerMeter, unused
        0,0,0,0,
        // LONG biYPelsPerMeter, unused
        0,0,0,0,
        // DWORD biClrUsed, the number of color indexes of palette, unused
        0,0,0,0,
        // DWORD biClrImportant, unused
        0,0,0,0
    ];

    var iPadding = (4 - ((biWidth * 3) % 4)) % 4;
    var aImgData = oData.data;
    var pixel_array = []
    var biWidth4 = biWidth<<2;
    var y = biHeight;

    do {
        var iOffsetY = biWidth4*(y-1);
        var strPixelRow = '';
        for (var x = 0; x < biWidth; x++) {
            var iOffsetX = x<<2;

            pixel_array.push(aImgData[iOffsetY+iOffsetX+2])
            pixel_array.push(aImgData[iOffsetY+iOffsetX+1])
            pixel_array.push(aImgData[iOffsetY+iOffsetX])
        }

        for (var c = 0; c < iPadding; c++) {
            pixel_array.push(0)
        }
    } while (--y);

    header = BITMAPFILEHEADER.concat(BITMAPINFOHEADER);
    strHeaderData = ''
    for (var i = 0; i < header.length; i ++) {
        strHeaderData += String.fromCharCode(header[i]);
    }

    var entire_uint8_data = new Uint8Array(BITMAPFILEHEADER.concat(BITMAPINFOHEADER).concat(pixel_array))

    return entire_uint8_data;
};

var run = () => {
    u("#imgSelect").on('change', (e) => {
       loadImage(document.getElementById("imgSelect")) 
    });
    u("#sendImg").on('click', (e) => {
        filename = document.getElementById('filename').value;
        fetch("http://192.168.0.177/ajax/loadImage?"+filename, {
            method: 'POST',
            mode: "no-cors",
            body: window.fullDataStr
        })
    });

}

if (document.readyState === 'loading') {  // Loading hasn't finished yet
  document.addEventListener('DOMContentLoaded', run());
} else {  // `DOMContentLoaded` has already fired
  run();
}


// NOT USED VVVVVVVVVV
var send_test_bmp = () => {
    red_canvas = document.createElement('canvas')
    red_canvas.id = "red canvas"
    red_canvas.width = 2
    red_canvas.height = 2
    red_ctx = red_canvas.getContext('2d')
    red_ctx.fillStyle = 'rgb(0,0,255)'
    red_ctx.fillRect(0,0,1,1)
    red_ctx.fillStyle = 'rgb(0,255,0)'
    red_ctx.fillRect(1,0,1,1)
    red_ctx.fillStyle = 'rgb(255,0,0)'
    red_ctx.fillRect(0,1,1,1)
    red_ctx.fillStyle = 'rgb(255,255,255)'
    red_ctx.fillRect(1,1,1,1)
    document.body.appendChild(red_canvas)
    data = red_ctx.getImageData(0,0,2,2)
    fullDataStr = genBitmapImage(data)

    fetch("http://192.168.0.177/ajax/loadImage?testttt.bmp", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/octet-stream',
        },
        mode: "no-cors",
        body: fullDataStr
    })
}

function formatData(ctx, width, height) {
    var image_rgb = []
    for(let j=0; j < width; j++) {
        let img_col = ctx.getImageData(j, 0, 1, height)
        let rgb_col = [];
        let arr_indx = 0
        for (let i=1; i <= height; i++) {
            let pixel = img_col.data.slice(arr_indx, i * 4).slice(0,3);
            arr_indx += 4;
            pixel_rgb = []
            pixel.forEach((val) => image_rgb.push(val));
//                 rgb_col.push(pixel_rgb)
//                 console.log(rgb_col);
        }
//             image_rgb.push(rgb_col);
    }
    console.log(image_rgb)
    console.log(JSON.stringify(image_rgb))
    var big_arr = []
    ctx.getImageData(0,0,canvas.width, canvas.height).data.forEach((val) => big_arr.push(val))
    console.log(JSON.stringify(big_arr))
    return image_rgb
}