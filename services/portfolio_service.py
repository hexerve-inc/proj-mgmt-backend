from sqlalchemy.orm import Session
from models.portfolio import Portfolio
from models.program import Program
from schemas.portfolio import PortfolioCreate, PortfolioUpdate
from typing import List, Optional

class PortfolioService:
    def __init__(self, db: Session):
        self.db = db

    def get_portfolios(self, skip: int = 0, limit: int = 100) -> List[Portfolio]:
        return self.db.query(Portfolio).filter(Portfolio.deleted_at.is_(None)).offset(skip).limit(limit).all()

    def get_portfolio(self, portfolio_id: str) -> Optional[Portfolio]:
        return self.db.query(Portfolio).filter(Portfolio.id == portfolio_id, Portfolio.deleted_at.is_(None)).first()

    def create_portfolio(self, portfolio_in: PortfolioCreate) -> Portfolio:
        db_portfolio = Portfolio(
            name=portfolio_in.name,
            description=portfolio_in.description
        )
        self.db.add(db_portfolio)
        self.db.commit()
        self.db.refresh(db_portfolio)

        if portfolio_in.program_ids:
            self.db.query(Program).filter(Program.id.in_(portfolio_in.program_ids)).update(
                {Program.portfolio_id: db_portfolio.id},
                synchronize_session=False
            )
            self.db.commit()
            self.db.refresh(db_portfolio)

        return db_portfolio

    def update_portfolio(self, portfolio_id: str, portfolio_in: PortfolioUpdate) -> Optional[Portfolio]:
        db_portfolio = self.get_portfolio(portfolio_id)
        if not db_portfolio:
            return None
        
        update_data = portfolio_in.model_dump(exclude_unset=True)
        program_ids = update_data.pop("program_ids", None)

        for field, value in update_data.items():
            setattr(db_portfolio, field, value)
        
        if program_ids is not None:
            # First, clear existing programs for this portfolio
            self.db.query(Program).filter(Program.portfolio_id == portfolio_id).update(
                {Program.portfolio_id: None},
                synchronize_session=False
            )
            # Then associate new ones
            if program_ids:
                self.db.query(Program).filter(Program.id.in_(program_ids)).update(
                    {Program.portfolio_id: portfolio_id},
                    synchronize_session=False
                )
        
        self.db.commit()
        self.db.refresh(db_portfolio)
        return db_portfolio

    def delete_portfolio(self, portfolio_id: str) -> bool:
        db_portfolio = self.get_portfolio(portfolio_id)
        if not db_portfolio:
            return False
        db_portfolio.soft_delete()
        self.db.commit()
        return True

