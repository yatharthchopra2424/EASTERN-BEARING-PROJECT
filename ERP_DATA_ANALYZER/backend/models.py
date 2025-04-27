from sqlalchemy import Column, Integer, String, Float, Index
from sqlalchemy.orm import declarative_base # Updated import

Base = declarative_base()

class ProductionRecordGRD(Base):
    __tablename__ = 'production_records_grd'
    # __bind_key__ is typically handled by the session/engine configuration,
    # not explicitly needed in the model definition with modern SQLAlchemy.

    id = Column(Integer, primary_key=True)
    shift_type = Column(String(10), nullable=True) # Increased size slightly
    posting_date = Column(String(20), nullable=True, index=True) # Index for faster date filtering
    document_no = Column(String(255), nullable=True, index=True) # Index if frequently filtered
    order_no = Column(String(255), nullable=True)
    item_no = Column(String(255), nullable=True)
    operation_no = Column(Integer, nullable=True)
    operation_description = Column(String(255), nullable=True)
    order_line_no = Column(Integer, nullable=True)
    type = Column(String(50), nullable=True)
    machine_no = Column(String(50), nullable=True, index=True) # Index for faster machine filtering
    current_c_t = Column(Float, nullable=True) # Cycle time often stored as float seconds
    output_quantity = Column(Integer, nullable=True)
    rejection_qty = Column(Integer, nullable=True)
    rejection_reason = Column(String(255), nullable=True)
    rework_qty = Column(Integer, nullable=True)
    rework_reason = Column(String(255), nullable=True)
    work_shift_code = Column(String(50), nullable=True, index=True) # Index for faster shift filtering
    start_time = Column(String(10), nullable=True) # Allow HH:MM or HH:MM:SS
    end_time = Column(String(10), nullable=True) # Allow HH:MM or HH:MM:SS
    plan_time = Column(Integer, nullable=True, default=0) # Plan time in seconds
    actual_run_time = Column(Integer, nullable=True, default=0) # Run time in seconds
    loss_time = Column(Integer, nullable=True, default=0) # Loss time in seconds
    remarks = Column(String(500), nullable=True) # Increased size for remarks
    operator_name = Column(String(255), nullable=True)
    loss_time_should_be = Column(Integer, nullable=True, default=0) # In seconds
    oee = Column(String(255), nullable=True) # Original OEE string, if needed for reference
    reason_code = Column(String(50), nullable=True)
    reason_time_hm = Column(Integer, nullable=True, default=0) # Assuming this is time in seconds now based on utility
    loss_time_remark = Column(String(500), nullable=True) # Increased size

    # Calculated fields (store results of calculations)
    availability = Column(Float, nullable=True)
    quality_rate = Column(Float, nullable=True)
    performance = Column(Float, nullable=True)
    oee_new = Column(Float, nullable=True, index=True) # Index the main OEE metric

    # Add more indexes if other columns are frequently used in WHERE clauses
    # Example: Index('ix_prodrecgrd_item_op', 'item_no', 'operation_no')

    def __repr__(self):
        return f"<ProductionRecordGRD(id={self.id}, date={self.posting_date}, machine={self.machine_no}, oee={self.oee_new})>"

# You can define other models for different databases/tables here
# class AnotherRecord(Base):
#     __tablename__ = 'another_table'
#     # __bind_key__ = 'another_db' # Specify if using a different bind
#     id = Column(Integer, primary_key=True)
#     name = Column(String(100))