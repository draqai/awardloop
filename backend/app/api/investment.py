# app/api/investment.py
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db

investment_bp = Blueprint('investment', __name__)

@investment_bp.route('/status', methods=['GET'])
@jwt_required()
def get_investment_status():
    """Get current user's investment status"""
    current_user_id = get_jwt_identity()['id']
    
    from app.models.user_investments import UserInvestment
    
    # Get active investments
    active_investments = UserInvestment.query.filter_by(
        user_id=current_user_id,
        investment_status='active'
    ).all()
    
    return jsonify({
        'success': True,
        'active_investments': [
            {
                'id': investment.id,
                'amount': float(investment.amount),
                'status': investment.investment_status,
                'activation_date': investment.activation_date.strftime('%Y-%m-%d %H:%M:%S') if investment.activation_date else None,
                'completion_date': investment.completion_date.strftime('%Y-%m-%d %H:%M:%S') if investment.completion_date else None
            } for investment in active_investments
        ]
    }), 200

@investment_bp.route('/history', methods=['GET'])
@jwt_required()
def get_investment_history():
    """Get current user's investment history"""
    current_user_id = get_jwt_identity()['id']
    
    from app.models.user_investments import UserInvestment
    
    # Get all investments
    investments = UserInvestment.query.filter_by(
        user_id=current_user_id
    ).order_by(UserInvestment.created_at.desc()).all()
    
    return jsonify({
        'success': True,
        'investments': [
            {
                'id': investment.id,
                'amount': float(investment.amount),
                'status': investment.investment_status,
                'activation_date': investment.activation_date.strftime('%Y-%m-%d %H:%M:%S') if investment.activation_date else None,
                'completion_date': investment.completion_date.strftime('%Y-%m-%d %H:%M:%S') if investment.completion_date else None,
                'created_at': investment.created_at.strftime('%Y-%m-%d %H:%M:%S')
            } for investment in investments
        ]
    }), 200