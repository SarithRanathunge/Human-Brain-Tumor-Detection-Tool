//Fetch the header.html and Footer.html when document loading
document.addEventListener("DOMContentLoaded", function () {
  fetch('header.html')
      .then(response => response.text())
      .then(data => {
          document.getElementById('header-placeholder').innerHTML = data;
          applyModeSettings();
        });
  fetch('footer.html')
        .then(response => response.text())
        .then(data => {
            document.getElementById('footer-placeholder').innerHTML = data;
          });

});


//Color mode changing 
function applyModeSettings() {
  var mode = document.getElementById("mode");
  var facebook = document.querySelectorAll(".facebook");
  var linkedIn = document.querySelectorAll(".linkedin");

  if (localStorage.getItem("theme") === "dark") {
      document.body.classList.add("dark-mode");
      mode.src = "images/sun.png";
      facebook.forEach(icon => icon.src = "images/white-facebook.png");
      linkedIn.forEach(icon => icon.src = "images/white-linkedin.png");
  } else {
      document.body.classList.remove("dark-mode");
      mode.src = "images/moon.png";
      facebook.forEach(icon => icon.src = "images/facebook.png");
      linkedIn.forEach(icon => icon.src = "images/linkedin.png");
  }

  mode.onclick = function () {
    document.body.classList.toggle("dark-mode");
    if (document.body.classList.contains("dark-mode")) {
        mode.src = "images/sun.png";
        facebook.forEach(icon => icon.src = "images/white-facebook.png");
        linkedIn.forEach(icon => icon.src = "images/white-linkedin.png");
        localStorage.setItem("theme", "dark");
    } else {
        mode.src = "images/moon.png";
        facebook.forEach(icon => icon.src = "images/facebook.png");
        linkedIn.forEach(icon => icon.src = "images/linkedin.png");
        localStorage.setItem("theme", "light");
    }
  };
}

//Image upload into web-page(drag and drop or upload)
const dropArea = document.getElementById("drop-area-section");
const inputFile = document.getElementById("input-file");
const imageShow = document.getElementById("image-show");

inputFile.addEventListener("change", uploadImage);

function uploadImage(){
    let imageLink =URL.createObjectURL(inputFile.files[0]);
    imageShow.style.backgroundImage = `url(${imageLink})`;
    imageShow.textContent = "";
    imageShow.style.border = 0;
}

dropArea.addEventListener("dragover", function(e){
    e.preventDefault();
});

dropArea.addEventListener("drop", function(e){
    e.preventDefault();
    inputFile.files = e.dataTransfer.files;
    uploadImage();
});

// Proceed button
const proceedButton = document.getElementById('proceed');
proceedButton.addEventListener('click', async function (event) {
    event.preventDefault()
    const fileInput = document.getElementById('input-file');
    const file = fileInput.files[0];

    if (!file) {
      alert('Please Upload MRI Scan image file (*PNG, *JPEG)');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/upload', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error('Network response was not ok.');
      }

      const result = await response.json();
      displayPopup(result);
    } catch (error) {
      console.error('Error:', error);
      alert('An error occurred. Please try again.');
    }
});

function displayPopup(data) {
    const popup = document.getElementById('popupWindow');
    const imageStages = document.getElementById('imageStages');
    const brainDimensions = document.getElementById('brainDimensions');
    const tumorDimensions = document.getElementById('tumorDimensions');
    const pdfLink = document.getElementById('pdfLink');

    // Clear existing content
    imageStages.innerHTML = '';
    
    // Display images
    data.imageUrls.forEach((imageUrl, index) => {
        const img = document.createElement('img');
        img.src = imageUrl;
        img.alt = `Stage ${index + 1}`;
        img.style.maxWidth = '100%'; // Ensure images fit within the popup
        img.style.height = 'auto';
        img.style.margin = '10px 0';
        imageStages.appendChild(img);
    });

    // Display dimensions
    brainDimensions.textContent = `Brain Width: ${data.brainDimensions.width}, Brain Height: ${data.brainDimensions.height}`;
    tumorDimensions.textContent = `Tumor Width: ${data.tumorDimensions.width}, Tumor Height: ${data.tumorDimensions.height}`;
    
    // Set PDF download link
    pdfLink.href = data.pdfUrl;
    pdfLink.style.display = 'block'; // Show the link
    
    // Display the popup
    popup.style.display = 'block';
}
//Image Slideshow Selecting
const selectingImage = document.getElementById('imageStages');
const proceedPopup = document.getElementById('popupWindow');
const imageWindow = document.getElementById('imagePopupWindow');

selectingImage.onclick = function(){
  proceedPopup.style.display = 'none';
  imageWindow.style.display = 'block';
  document.getElementById('image-scaling').src = 'processed/stage_1.png';
}

//Close Proceed Popup Windows
function closeProceedPopup() {
  proceedPopup.style.display = 'none';
}

//document.getElementById('imagePopupWindow').style.display = 'none';
//Image Slideshow Selecting
function closeImagePopup(){
  imageWindow.style.display = 'none';
  proceedPopup.style.display = 'block'
}

//slide-show left side or right side
const processedImages = ['stage_1.png', 'stage_2.png', 'stage_3.png', 'stage_4.png', 'stage_5.png', 'stage_6.png', 'stage_7.png', 'stage_8.png'];
const imageElement = document.getElementById('image-scaling'); // Use getElementById for specific ID
const leftArrow = document.querySelector('.left-arrow');
const rightArrow = document.querySelector('.right-arrow');
const imageTopic = document.querySelector('.image-name')
let currentIndex = 0;

function updateImage(){
  switch(currentIndex){
    case 0:
      imageTopic.textContent = "Gray-scale Image";
      break;
    case 1:
      imageTopic.textContent = "Sharpened Image";
      break;
    case 2:
      imageTopic.textContent = "Segmented Image";
      break;
    case 3:
      imageTopic.textContent ="Eroded Image";
      break;
    case 4:
      imageTopic.textContent ="Dilated Image";
      break;
    case 5:
      imageTopic.textContent ="Highlighted Tumor Region";
      break;
    case 6:
      imageTopic.textContent ="Contours of the Brain";
      break;
    case 7:
      imageTopic.textContent ="Tumor range";
      break;
  }
  imageElement.src = `processed/${processedImages[currentIndex]}`;
}

rightArrow.onclick = function() {
  currentIndex = currentIndex + 1;
  if(currentIndex < processedImages.length){
    updateImage();
  }else{
    currentIndex = 0;
    updateImage();
  }
};

leftArrow.onclick = function() {
  currentIndex = currentIndex - 1;
  if(currentIndex > 0){
    updateImage();
  }else{
    currentIndex = processedImages.length - 1;
    updateImage();
  }
};