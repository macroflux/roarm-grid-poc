"""
Simple script to test which camera indices are available and display their feeds.
Press 'q' to move to the next camera, or ESC to exit.
"""
import cv2

def test_camera_index(index):
    """Test if a camera exists at the given index."""
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        return False, None
    
    # Try to read a frame
    ret, frame = cap.read()
    cap.release()
    return ret, frame

def main():
    print("Scanning for available cameras...")
    available_cameras = []
    
    # Test indices 0-5 (usually enough for most systems)
    for i in range(6):
        ret, frame = test_camera_index(i)
        if ret:
            height, width = frame.shape[:2]
            print(f"✓ Camera {i}: Available ({width}x{height})")
            available_cameras.append(i)
        else:
            print(f"✗ Camera {i}: Not available")
    
    if not available_cameras:
        print("\nNo cameras found!")
        return
    
    print(f"\nFound {len(available_cameras)} camera(s): {available_cameras}")
    print("\nNow testing each camera with live preview...")
    print("Press 'q' to move to next camera, or ESC to exit\n")
    
    for idx in available_cameras:
        cap = cv2.VideoCapture(idx)
        if not cap.isOpened():
            continue
            
        print(f"Showing Camera {idx} - Press 'q' for next camera, ESC to exit")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print(f"Failed to read from camera {idx}")
                break
            
            # Add text overlay
            cv2.putText(frame, f"Camera Index: {idx}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, "Press 'q' for next, ESC to exit", (10, 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            cv2.imshow(f"Camera Test", frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):  # Move to next camera
                break
            elif key == 27:  # ESC to exit
                cap.release()
                cv2.destroyAllWindows()
                return
        
        cap.release()
    
    cv2.destroyAllWindows()
    print("\nCamera test complete!")
    print(f"Available cameras: {available_cameras}")

if __name__ == "__main__":
    main()
