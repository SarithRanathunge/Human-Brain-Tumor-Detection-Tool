from flask import Flask, request, jsonify, send_from_directory, send_file
import os
import cv2
import numpy as np
from fpdf import FPDF

app = Flask(__name__, static_folder='')

UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    #Display the image in the image path
    Brain_tumor_image = cv2.imread(file_path)
    
    #Use bicubic interpolation to scale the image (upsize)
    scale_percent = 200
    width = int(Brain_tumor_image.shape[1] * scale_percent / 100)
    height = int(Brain_tumor_image.shape[0] * scale_percent / 100)
    dimensions = (width, height)
    Resized_brain_tumor_image = cv2.resize(Brain_tumor_image, dimensions, interpolation=cv2.INTER_CUBIC)

    #Convert the above image to a grayscale image for better processing
    Brain_tumor_image_grayscale = cv2.cvtColor(Resized_brain_tumor_image, cv2.COLOR_BGR2GRAY)

    # Define a Laplacian sharpening kernel
    kernel = np.array([[0, -0.4, 0],
                   [-0.4, 3, -0.4],
                   [0, -0.4, 0]])

    sharpened_image_of_brain_tumor = cv2.filter2D(src=Brain_tumor_image_grayscale, ddepth=-1, kernel=kernel)

    # Convert the sharpened image to binary using thresholding
    ret, binary_image_of_brain = cv2.threshold(Brain_tumor_image_grayscale, 150, 255, cv2.THRESH_BINARY)

    # Define a kernel size for morphological operations
    kernel = np.ones((3, 3), np.uint8)

    # Erode the image to remove the skull outline
    eroded_image = cv2.erode(binary_image_of_brain, kernel, iterations=10)

    # Dilate the image to restore the tumor to its original size
    dilated_image = cv2.dilate(eroded_image, kernel, iterations=10)

    #fill the dilated image in red colour and display it on the original image
    contours_of_tumor, _ = cv2.findContours(dilated_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    mask = np.zeros_like(Resized_brain_tumor_image)
    for contour in contours_of_tumor:
        cv2.drawContours(mask, [contour], -1, (0, 0, 255), thickness=cv2.FILLED)
    highlighted_tumor_image = cv2.addWeighted(Resized_brain_tumor_image, 0.7, mask, 0.3, 0)

    #create a copy of the sharpened image
    sharpened_image_copy = sharpened_image_of_brain_tumor.copy()

    #create a binary threshold on the copy image
    ret, binary_image_copy_of_brain_for_contours = cv2.threshold(sharpened_image_copy, 230, 255, cv2.THRESH_BINARY)

    # Find contours using OpenCV
    contours, hierarchy = cv2.findContours(binary_image_copy_of_brain_for_contours, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # Create a copy of the original grayscale image to draw contours
    contour_image_of_brain = binary_image_copy_of_brain_for_contours.copy()
    contour_image_of_brain = cv2.cvtColor(contour_image_of_brain, cv2.COLOR_GRAY2BGR)  # Convert to BGR for color drawing

    # Draw the contours on the grayscale image
    cv2.drawContours(contour_image_of_brain, contours, -1, (0, 255, 0), 2)  # Green color, thickness 2

    #print the resolution (length and width) of the image
    print(sharpened_image_of_brain_tumor.shape)

    #create a copy of the sharpened image
    sharpened_image_copy_for_calculations = sharpened_image_of_brain_tumor.copy()

    #create a binary threshold on the copy image
    ret, binary_image_copy_of_brain_for_calculations = cv2.threshold(sharpened_image_copy_for_calculations, 45, 255, cv2.THRESH_BINARY)

    #Find the outer contour of the brain
    brain_outer_contours, _ = cv2.findContours(binary_image_copy_of_brain_for_calculations, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contour_image_of_outer_brain = binary_image_copy_of_brain_for_calculations.copy()
    contour_image_of_outer_brain = cv2.cvtColor(contour_image_of_outer_brain, cv2.COLOR_GRAY2BGR)  # Convert to BGR for color drawing
    cv2.drawContours(contour_image_of_outer_brain, contours, -1, (0, 255, 0), 2)  # Green color, thickness 2

    #Find the largest contour of the image
    largest_contour = max(brain_outer_contours, key=cv2.contourArea)

    # Get the bounding box of the largest contour
    x, y, width_of_brain, height_of_brain = cv2.boundingRect(largest_contour)

    #draw the bounding box
    contoured_brain = contour_image_of_outer_brain.copy()
    brain_with_bounding_box = cv2.rectangle(contoured_brain, (x, y), (x + width_of_brain, y + height_of_brain), (0, 255, 0), 2)  # Green rectangle, thickness 2

    #Makes variables to store average human brain size
    average_brain_height_in_mm = 167
    average_brain_width_in_mm = 140

    #Make variables of the image resoultion
    image_height_in_pixels = sharpened_image_of_brain_tumor.shape[0]
    image_width_in_pixels = sharpened_image_of_brain_tumor.shape[1]

    #Make variables of the brain height and width in pixels
    brain_height_in_pixels = height_of_brain
    brain_width_in_pixels = width_of_brain

    # Calculate scale factors
    scale_factor_height = average_brain_height_in_mm / image_height_in_pixels
    scale_factor_width = average_brain_width_in_mm / image_width_in_pixels

    # Convert pixel measurements to real-world measurements
    real_world_height_of_brain = brain_height_in_pixels * scale_factor_height
    real_world_width_of_brain = brain_width_in_pixels * scale_factor_width

    # # Assuming you have the sharpened_image_copy ready
    # Apply binary thresholding to get a binary image
    ret, binary_image_copy_of_tumor = cv2.threshold(sharpened_image_copy, 230, 255, cv2.THRESH_BINARY)

    # Find contours in the binary dilated image
    contours, hierarchy = cv2.findContours(dilated_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Check if a contour for the tumor is available or not
    if (len(contours)==0):  #If no contour, no tumor
        largest_contour = 0
        height_of_tumor=0
        width_of_tumor=0
        print("There is no tumor in the brain")
        # Print the height and width of the tumor
        print(f'Height of the tumor: {height_of_tumor} pixels')
        print(f'Width of the tumor: {width_of_tumor} pixels')

        # Given pixel dimensions of the tumor
        tumor_pixel_height = height_of_tumor  # in pixels
        tumor_pixel_width = width_of_tumor   # in pixels

        # Assuming scale factors are defined
        scale_factor_height_for_tumor = scale_factor_height  # Replace with the actual scale factor for height
        scale_factor_width_for_tumor = scale_factor_width   # Replace with the actual scale factor for width

        # Convert pixel measurements to real-world measurements
        tumor_real_world_height = tumor_pixel_height * scale_factor_height_for_tumor
        tumor_real_world_width = tumor_pixel_width * scale_factor_width_for_tumor

        tumor_with_bounding_box = Resized_brain_tumor_image.copy()
    else: #There is a countour for the tumor
        largest_contour = max(contours, key=cv2.contourArea)

        # Get the bounding box of the largest contour
        x, y, width, height = cv2.boundingRect(largest_contour)

        # Draw the bounding box on the binary image for visualization
        tumor_image = cv2.cvtColor(Brain_tumor_image_grayscale, cv2.COLOR_GRAY2BGR)  # Convert to BGR for color drawing
        tumor_with_bounding_box = cv2.rectangle(tumor_image, (x, y), (x + width, y + height), (0, 0, 255), 2)  # Red rectangle, thickness 2

        # Print the height and width of the tumor
        print(f'Height of the tumor: {height} pixels')
        print(f'Width of the tumor: {width} pixels')

        # Given pixel dimensions of the tumor
        tumor_pixel_height = height  # in pixels
        tumor_pixel_width = width   # in pixels

        # Assuming scale factors are defined
        scale_factor_height_for_tumor = scale_factor_height  # Replace with the actual scale factor for height
        scale_factor_width_for_tumor = scale_factor_width   # Replace with the actual scale factor for width

        # Convert pixel measurements to real-world measurements
        tumor_real_world_height = tumor_pixel_height * scale_factor_height_for_tumor
        tumor_real_world_width = tumor_pixel_width * scale_factor_width_for_tumor
    
    #Area of the brain
    Area_of_the_brain = real_world_height_of_brain * real_world_width_of_brain

    #Area of the tumor
    Area_of_the_tumor = tumor_real_world_height * tumor_real_world_width

    Percentage_of_tumor_in_brain = (Area_of_the_tumor / Area_of_the_brain) * 100

    #identify the stage of the tumor based on internet information
    tumor_stage = ""
    if (Area_of_the_tumor/100) == 0:
        tumor_stage = "No Tumor"
    elif (Area_of_the_tumor/100) > 0 and (Area_of_the_tumor/100) < 3.5:
        tumor_stage = "Grade 1 Tumor"
    elif (Area_of_the_tumor/100) >= 3.5 and (Area_of_the_tumor/100) < 13:
        tumor_stage = "Grade 2 Tumor"
    elif (Area_of_the_tumor/100) >= 13 and (Area_of_the_tumor/100) < 25:
        tumor_stage = "Grade 3 Tumor"
    elif (Area_of_the_tumor/100) >= 25:
        tumor_stage = "Grade 4 Tumor"
    print(tumor_stage)
    #print results (areas)
    print(f"Percentage of the tumor in the brain: {Percentage_of_tumor_in_brain:.2f}%")
    print(f"Area of the tumor: {Area_of_the_tumor:.2f} squared mm")
    print(f"Area of the brain: {Area_of_the_brain:.2f} squared mm")

    # Create and save the images for the 8 stages
    stage_images = []
    for i, stage_image in enumerate([Resized_brain_tumor_image, sharpened_image_of_brain_tumor, binary_image_of_brain, eroded_image, dilated_image, highlighted_tumor_image, brain_with_bounding_box, tumor_with_bounding_box]):
        stage_path = os.path.join(PROCESSED_FOLDER, f'stage_{i+1}.png')
        cv2.imwrite(stage_path, stage_image)
        stage_images.append(stage_path)

    # Save the highlighted tumor image to a temporary file
    highlighted_tumor_path = os.path.join(PROCESSED_FOLDER, 'highlighted_tumor.png')
    cv2.imwrite(highlighted_tumor_path, highlighted_tumor_image)

    # Save the final report as a PDF
    pdf_path = os.path.join(PROCESSED_FOLDER, 'tumor_report.pdf')
    pdf = FPDF()
    pdf.add_page()

    # Set fill color for the header (dark blue)
    pdf.set_fill_color(0, 0, 139)
    pdf.rect(0, 0, 210, 25, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", size=18, style='B')
    pdf.cell(0, 5, 'Tumor Detection Summary Report', ln=True, align='C', fill=True)

    pdf.set_text_color(0, 0, 0)
    pdf.set_xy(10, 35)
    pdf.set_font("Courier", size=9)
    pdf.cell(0, 10, 'The following image shows the tumor highlighted in red:', ln=True, align='C')
    pdf.image(highlighted_tumor_path, x=62, y=50, w=80)

    # Add measurements text below images
    # Set the position for the table
    pdf.set_xy(10, 160)

    # Set the font for the table headers
    pdf.set_font("Courier", size=10, style='B')
    pdf.set_fill_color(43, 77, 243)
    pdf.set_text_color(255, 255, 255)
    # Define the headers
    headers = ['Description', 'Value (cm)']

    # Create header cells
    for header in headers:
        pdf.cell(90, 10, header, border=1, align="C", fill=True)
    pdf.ln()

    
    # Set the font for the table data
    pdf.set_font("Courier", size=10)
    pdf.set_text_color(0, 0, 0)

    # Define the data
    data = [
    ('Tumor Height', f'{tumor_real_world_height/10:.2f} cm'),
    ('Tumor Width', f'{tumor_real_world_width/10:.2f} cm'),
    ('Brain Height', f'{real_world_height_of_brain/10:.2f} cm'),
    ('Brain Width', f'{real_world_width_of_brain/10:.2f} cm'),
    ('Area of the tumor', f'{Area_of_the_tumor/100:.2f} square centimeters'),
    ('Area of the brain', f'{Area_of_the_brain/100:.2f} square centimeters'),
    ('Percentage of the tumor in the brain', f'{Percentage_of_tumor_in_brain:.2f} %')
    ]

    # Create data cells
    for description, value in data:
        pdf.cell(90, 10, description, border=1, align="C")
        pdf.cell(90, 10, value, border=1, align="C")
        pdf.ln()
    
    # Create a cell for tumor stage
    pdf.set_xy(10, 260)
    pdf.set_font("Courier", size=10, style='B')
    pdf.set_fill_color(43, 77, 243)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(90, 10, 'Tumor Stage', border=1, align="C", fill=True)
    pdf.set_font("Courier", size=10, style='B')
    pdf.set_text_color(0, 0, 0)
    pdf.cell(90, 10, tumor_stage, border=1, align="C")
    pdf.ln()

    pdf.output(pdf_path)

    processed_path = os.path.join(PROCESSED_FOLDER, 'processed_image_2.png')
    cv2.imwrite(processed_path,  tumor_with_bounding_box)

    return jsonify({'imageUrls': [f'/processed/{os.path.basename(img)}' for img in stage_images], 'pdfUrl': '/processed/tumor_report.pdf', "tumorDimensions": {"height": f'{tumor_real_world_height/10:.2f} cm',
      'width': f'{tumor_real_world_width/10:.2f} cm',}, "brainDimensions": {"height": f'{real_world_height_of_brain/10:.2f} cm',
      'width': f'{real_world_width_of_brain/10:.2f} cm',}})
@app.route('/processed/<filename>')
def get_processed_image(filename):
    return send_from_directory(PROCESSED_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
