import cv2
import numpy as np

def preprocess_for_ocr(img):
    """
    Bước 1: Chuyển xám, tăng độ tương phản và khử nhiễu
    """
    # Kiểm tra nếu ảnh đã là ảnh xám thì không convert nữa
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img
        
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    denoised = cv2.bilateralFilter(enhanced, 9, 75, 75)
    return denoised

def clean_plate_noise(img_bin):
    """
    Bước 2: Giữ lại các thành phần giống ký tự, loại bỏ nhiễu (ốc vít, viền, bụi)
    Input: Ảnh nhị phân (Chữ trắng, nền đen)
    Output: Mask sạch (Chữ trắng, nền đen)
    """
    contours, _ = cv2.findContours(img_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    mask = np.zeros_like(img_bin)
    h_img, w_img = img_bin.shape
    
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        aspect_ratio = w / float(h)
        solidity = cv2.contourArea(c) / float(w * h)
        height_ratio = h / float(h_img)
        
        keep = False
        # Logic lọc nhiễu:
        # 1. Chiều cao ký tự phải đủ lớn (> 30% dòng)
        # 2. Tỷ lệ W/H hợp lý (0.05 - 1.0) -> Chấp nhận cả số 1
        # 3. Độ đặc (Solidity) > 0.1
        if height_ratio > 0.3: 
            if 0.05 < aspect_ratio < 1.0: 
                if solidity > 0.10:
                    keep = True
        
        if keep:
            cv2.drawContours(mask, [c], -1, 255, -1)
            
    return mask

def crop_vertical_borders(img_bin):
    """
    Bước 3: Cắt bỏ khoảng trống thừa bên trái và bên phải
    """
    h, w = img_bin.shape
    col_sums = np.sum(img_bin, axis=0) # Cộng pixel theo cột
    col_indices = np.where(col_sums > 0)[0]
    
    if len(col_indices) > 0:
        x_min = max(0, col_indices[0] - 2) # Padding nhẹ 2px
        x_max = min(w, col_indices[-1] + 2)
        return img_bin[:, x_min:x_max]
    
    return img_bin

def find_split_point(img_binary):
    """
    Bước 4: Tìm khe hở ngang tốt nhất để cắt dòng
    """
    h, w = img_binary.shape
    row_sums = np.sum(img_binary, axis=1)
    
    # Chỉ tìm trong khoảng giữa (30% -> 70% chiều cao)
    start_search = int(h * 0.30)
    end_search = int(h * 0.70)
    
    min_val = np.inf
    split_index = h // 2
    
    for i in range(start_search, end_search):
        if row_sums[i] < min_val:
            min_val = row_sums[i]
            split_index = i
            
    return split_index

def deskew(img_gray):
    """
    Tự động xoay thẳng ảnh dựa trên góc nghiêng của các khối pixel
    Input: Ảnh xám (Grayscale)
    Output: Ảnh xám đã xoay thẳng
    """
    # 1. Threshold để tìm các điểm trắng (chữ/viền)
    _, thresh = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # 2. Tìm toạ độ tất cả điểm trắng
    coords = np.column_stack(np.where(thresh > 0))
    
    # 3. Tìm hình chữ nhật bao quanh tối thiểu (Rotated Rectangle)
    angle = cv2.minAreaRect(coords)[-1]
    
    # 4. Chuẩn hóa góc quay (OpenCV trả về góc từ -90 đến 0)
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
        
    # Chỉ xoay nếu nghiêng đáng kể (> 1 độ) để đỡ tốn CPU
    if abs(angle) < 1:
        return img_gray

    # 5. Xoay ảnh
    (h, w) = img_gray.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(img_gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    
    return rotated

def split_plate(plate_img):
    """
    Hàm chính điều phối quy trình cắt và làm sạch
    """
    # 1. Đảm bảo input là ảnh xám (dù preprocess đã làm, check lại cho chắc)
    if len(plate_img.shape) == 3:
        gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
    else:
        gray = plate_img
        
    gray = deskew(gray)

    h, w = gray.shape
    ratio = h / w
    
    # 2. Tạo ảnh nhị phân nền (Otsu Threshold)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    parts = []
    
    # == TRƯỜNG HỢP 1: BIỂN VUÔNG (2 DÒNG) ==
    if ratio > 0.5: 
        # A. Tìm vị trí cắt
        split_point = find_split_point(thresh)
        
        # B. Cắt ảnh thành 2 phần
        top_part = thresh[0:split_point, :]
        bot_part = thresh[split_point:h, :]
        
        # C. Làm sạch từng phần (Xóa ốc vít, cắt viền)
        top_clean = clean_plate_noise(top_part)
        bot_clean = clean_plate_noise(bot_part)
        
        # D. Cắt sát lề
        top_final = crop_vertical_borders(top_clean)
        bot_final = crop_vertical_borders(bot_clean)
        
        # E. Đảo màu (Chữ đen, nền trắng) cho EasyOCR
        top_final = cv2.bitwise_not(top_final)
        bot_final = cv2.bitwise_not(bot_final)
        
        parts = [top_final, bot_final]
        return True, parts
    
    # == TRƯỜNG HỢP 2: BIỂN DÀI (1 DÒNG) ==
    else: 
        clean = clean_plate_noise(thresh)
        final = crop_vertical_borders(clean)
        final = cv2.bitwise_not(final) # Đảo màu
        
        return False, [final]

def draw_result(frame, text, box):
    x1, y1, x2, y2 = box
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
    cv2.putText(frame, text, (x1, y1-10), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    return frame