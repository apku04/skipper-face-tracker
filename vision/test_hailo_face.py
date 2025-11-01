#!/usr/bin/env python3
"""
Quick test to see if we can load and run Hailo face detection models.
Tests both yolov5s_personface and scrfd models.
"""
import cv2
import numpy as np
from hailo_platform import (VDevice, HailoStreamInterface, InferVStreams, ConfigureParams,
                            InputVStreamParams, OutputVStreamParams, FormatType)

# Available face detection models
MODELS = {
    "yolov5_personface": "/usr/share/hailo-models/yolov5s_personface_h8l.hef",
    "scrfd": "/usr/share/hailo-models/scrfd_2.5g_h8l.hef"
}

def test_model_load(model_path):
    """Test if we can load and configure a Hailo model"""
    try:
        print(f"\nTesting: {model_path}")
        
        # Create VDevice
        params = VDevice.create_params()
        vdevice = VDevice(params)
        print(f"✓ VDevice created")
        
        # Load HEF
        from hailo_platform import HEF
        hef = HEF(model_path)
        print(f"✓ HEF loaded: {model_path}")
        
        # Get network group
        configure_params = ConfigureParams.create_from_hef(hef, interface=HailoStreamInterface.PCIe)
        network_group = vdevice.configure(hef, configure_params)[0]
        print(f"✓ Network group configured")
        
        # Get network info
        network_names = hef.get_network_group_names()
        print(f"✓ Network groups: {network_names}")
        
        # Get input/output stream info
        input_vstream_infos = hef.get_input_vstream_infos()
        output_vstream_infos = hef.get_output_vstream_infos()
        
        print(f"  Input vstreams: {len(input_vstream_infos)}")
        for inp in input_vstream_infos:
            print(f"    {inp.name}: shape={inp.shape}, format={inp.format}")
        
        print(f"  Output vstreams: {len(output_vstream_infos)}")
        for out in output_vstream_infos:
            print(f"    {out.name}: shape={out.shape}, format={out.format}")
        
        return True, vdevice, hef, network_group
        
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None, None, None

def test_inference(vdevice, hef, network_group, test_image_path=None):
    """Try a single inference pass"""
    try:
        print("\n--- Testing inference ---")
        
        # Activate network group
        network_group.activate()
        print("✓ Network group activated")
        
        # Get input/output params
        input_vstreams_params = InputVStreamParams.make_from_network_group(network_group, quantized=False, format_type=FormatType.FLOAT32)
        output_vstreams_params = OutputVStreamParams.make_from_network_group(network_group, quantized=False, format_type=FormatType.FLOAT32)
        
        # Get expected input shape
        input_info = hef.get_input_vstream_infos()[0]
        height, width, channels = input_info.shape
        print(f"Expected input: {height}x{width}x{channels}")
        
        # Create dummy input (or load image if provided)
        if test_image_path and cv2:
            frame = cv2.imread(test_image_path)
            if frame is not None:
                frame = cv2.resize(frame, (width, height))
                # Convert BGR to RGB
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                print(f"✓ Loaded test image: {test_image_path}")
        else:
            # Create random test data
            frame = np.random.randint(0, 255, (height, width, channels), dtype=np.uint8)
            print(f"✓ Created dummy input")
        
        # Convert to float32 and normalize (typical for YOLO models)
        input_data = frame.astype(np.float32) / 255.0
        
        # Add batch dimension if needed - reshape to (batch, height, width, channels)
        if len(input_data.shape) == 3:
            input_data = np.expand_dims(input_data, axis=0)
        print(f"  Input shape: {input_data.shape}")
        
        # Infer
        with InferVStreams(network_group, input_vstreams_params, output_vstreams_params) as infer_pipeline:
            print("✓ Inference pipeline created")
            
            # Single inference - use vstream name directly
            input_name = hef.get_input_vstream_infos()[0].name
            input_dict = {input_name: input_data}
            output_dict = infer_pipeline.infer(input_dict)
            
            print(f"✓ Inference completed!")
            print(f"  Output keys: {list(output_dict.keys())}")
            for key, value in output_dict.items():
                print(f"    {key}: shape={value.shape}, dtype={value.dtype}")
            
            return True
            
    except Exception as e:
        print(f"✗ Inference failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("Hailo Face Detection Model Test")
    print("=" * 60)
    
    for name, path in MODELS.items():
        print(f"\n{'='*60}")
        print(f"Model: {name}")
        print(f"{'='*60}")
        
        success, vdevice, hef, network_group = test_model_load(path)
        
        if success:
            # Try inference
            test_inference(vdevice, hef, network_group)
        
        print()

if __name__ == "__main__":
    main()
