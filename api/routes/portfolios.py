from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from api.deps import get_db, get_current_user, require_permission
from schemas.portfolio import PortfolioCreate, PortfolioUpdate, PortfolioResponse
from services.portfolio_service import PortfolioService
from models.user import User

router = APIRouter()

@router.get("/", response_model=List[PortfolioResponse], dependencies=[Depends(require_permission("portfolios:read"))])
def read_portfolios(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = PortfolioService(db)
    return service.get_portfolios(skip=skip, limit=limit)

@router.post("/", response_model=PortfolioResponse, dependencies=[Depends(require_permission("portfolios:create"))])
def create_portfolio(
    portfolio_in: PortfolioCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = PortfolioService(db)
    return service.create_portfolio(portfolio_in)

@router.get("/{portfolio_id}", response_model=PortfolioResponse)
def read_portfolio(
    portfolio_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    checker = Depends(require_permission("portfolios:read"))
):
    checker.check_scope("portfolio", portfolio_id)
    service = PortfolioService(db)
    portfolio = service.get_portfolio(portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio

@router.put("/{portfolio_id}", response_model=PortfolioResponse)
def update_portfolio(
    portfolio_id: str,
    portfolio_in: PortfolioUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    checker = Depends(require_permission("portfolios:update"))
):
    checker.check_scope("portfolio", portfolio_id)
    service = PortfolioService(db)
    portfolio = service.update_portfolio(portfolio_id, portfolio_in)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio

@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio(
    portfolio_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    checker = Depends(require_permission("portfolios:delete"))
):
    checker.check_scope("portfolio", portfolio_id)
    service = PortfolioService(db)
    if not service.delete_portfolio(portfolio_id):
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return None
