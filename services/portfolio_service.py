from sqlalchemy.orm import Session
from models.portfolio import Portfolio
from schemas.portfolio import PortfolioCreate, PortfolioUpdate
from typing import List, Optional

class PortfolioService:
    def __init__(self, db: Session):
        self.db = db

    def get_portfolios(self, skip: int = 0, limit: int = 100) -> List[Portfolio]:
        return self.db.query(Portfolio).offset(skip).limit(limit).all()

    def get_portfolio(self, portfolio_id: str) -> Optional[Portfolio]:
        return self.db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()

    def create_portfolio(self, portfolio_in: PortfolioCreate) -> Portfolio:
        db_portfolio = Portfolio(
            name=portfolio_in.name,
            description=portfolio_in.description
        )
        self.db.add(db_portfolio)
        self.db.commit()
        self.db.refresh(db_portfolio)
        return db_portfolio

    def update_portfolio(self, portfolio_id: str, portfolio_in: PortfolioUpdate) -> Optional[Portfolio]:
        db_portfolio = self.get_portfolio(portfolio_id)
        if not db_portfolio:
            return None
        
        update_data = portfolio_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_portfolio, field, value)
        
        self.db.commit()
        self.db.refresh(db_portfolio)
        return db_portfolio

    def delete_portfolio(self, portfolio_id: str) -> bool:
        db_portfolio = self.get_portfolio(portfolio_id)
        if not db_portfolio:
            return False
        self.db.delete(db_portfolio)
        self.db.commit()
        return True

