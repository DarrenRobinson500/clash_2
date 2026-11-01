from datetime import datetime, timedelta
from account import *
from nav import *
from read import builder_time

# image_1 = [builder_panel, 480, 20, 280, 250]
# image_2 = [builder_base_panel, 550, 20, 280, 250]
# images = [image_1, image_2]
# time_region = [130, 30, 150, 30]

def get_status(accounts=Accounts):
    print("\nGetting status")
    os.makedirs(os.path.join(BASE_DIR, 'images', 'status'), exist_ok=True)

    tx, ty, tw, th = time_region
    tmpl_gray = cv2.cvtColor(upgrades_in_progress.image, cv2.COLOR_BGR2GRAY)
    lh, lw = tmpl_gray.shape

    account_columns = []
    time_columns = []
    times = []
    for account in accounts:
        account.switch()
        crops = []
        time_crops = []
        for loc, x, y, w, h in images:
            if loc == builder_panel:
                account.collect_resources()
            if loc == builder_base_panel:
                account.collect_builder_resources()
            go(loc)
            origin = game_screenshot_origin()
            if origin is None:
                crop = np.zeros((h, w, 3), dtype=np.uint8)
            else:
                crop = screenshot_region((origin[0] + x, origin[1] + y), w, h)
            crops.append(crop)

            res = cv2.matchTemplate(cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY), tmpl_gray, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, (mx, my) = cv2.minMaxLoc(res)
            if max_val >= 0.8:
                slc = crop[my + ty: my + ty + th, mx + tx: mx + tx + tw]
                time_crop = np.zeros((th, tw, 3), dtype=np.uint8)
                time_crop[:slc.shape[0], :slc.shape[1]] = slc
            else:
                time_crop = np.zeros((th, tw, 3), dtype=np.uint8)
            time_crops.append(time_crop)

            gray_crop = cv2.cvtColor(time_crop, cv2.COLOR_BGR2GRAY)
            chars = builder_time._find_chars(gray_crop)
            chars.sort(key=lambda c: c[1])
            raw = ''.join(c for _, _, _, c in chars)
            parts = re.findall(r'\d+[hms]', raw)
            times.append(''.join(parts) if parts else None)

        account_columns.append(np.vstack(crops))
        time_columns.append(np.vstack(time_crops))

    combined = np.hstack(account_columns)

    result = datetime.now() + timedelta(seconds=min(
        sum(int(n) * {'h': 3600, 'm': 60, 's': 1}[u] for n, u in re.findall(r'(\d+)([hms])', t))
        for t in times if t
    )) if any(times) else None

    if result:
        label = f"{format_time(datetime.now())} -> {format_time(result)}"
        header = np.zeros((30, combined.shape[1], 3), dtype=np.uint8)
        cv2.putText(header, label, (5, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        combined = np.vstack([header, combined])

    cv2.imwrite(os.path.join(BASE_DIR, 'images', 'status', 'status.jpg'), combined)
    cv2.imwrite(r'C:\Users\darre\OneDrive\Hobbies\Clash\status.jpg', combined)

    status_times = np.hstack(time_columns)
    cv2.imwrite(os.path.join(BASE_DIR, 'images', 'status', 'status_times.jpg'), status_times)

    return result


def format_time(dt):
    time_str = dt.strftime('%I:%M%p').lstrip('0').lower()
    if dt - datetime.now() < timedelta(hours=24):
        return time_str
    return f"{dt.day} {dt.strftime('%B')} {time_str}"
