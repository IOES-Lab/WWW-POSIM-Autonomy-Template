"""Stock BlueROV2 allocation in ENU/body coordinates, forces in newtons."""
def allocate(forward,turn,vertical):
    clamp=lambda v:max(-20.,min(20.,v))
    # Joint local axes are -Z. Horizontal link rotations give X directions
    # [-,-,+,+], and positive yaw torques [-,+,+,-]. Vertical axes point down.
    return [clamp(-forward-turn),clamp(-forward+turn),clamp(forward+turn),clamp(forward-turn),clamp(-vertical),clamp(-vertical)]
