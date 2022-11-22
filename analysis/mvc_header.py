class MVCExtension:
    def __init__(self, non_idr_flag: int, priority_id: int, view_id: int, temporal_id: int, anchor_pic_flag: int, inter_view_flag: int, reserved_one_bit: int) -> None:
        self.non_idr_flag: int = non_idr_flag
        self.priority_id: int = priority_id
        self.view_id: int = view_id
        self.temporal_id: int = temporal_id
        self.anchor_pic_flag: int = anchor_pic_flag
        self.inter_view_flag: int = inter_view_flag
        self.reserved_one_bit: int = reserved_one_bit
    
    def __str__(self) -> str:
        return str(vars(self))
