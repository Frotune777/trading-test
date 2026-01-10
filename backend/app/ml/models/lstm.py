"""
LSTM Model for Stock Prediction

Implements LSTM classifier for time-series stock direction prediction.
Uses 2-layer LSTM architecture with dropout for regularization.

Ported from trader_start/libs/lstm_model.py
Author: Trading System ML Team
Created: 2026-01-09
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
from typing import Dict, Tuple, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class LSTMClassifier(nn.Module):
    """
    LSTM-based classifier for stock prediction.
    
    Architecture:
        Input(features, timesteps) → LSTM(128) → Dropout(0.2) → 
        LSTM(64) → Dropout(0.2) → Dense(32) → Dropout(0.1) → 
        Dense(num_classes)
    
    Example:
        >>> model = LSTMClassifier(input_size=47, num_classes=3)
        >>> x = torch.randn(32, 20, 47)  # batch, seq_len, features
        >>> output = model(x)
        >>> print(output.shape)  # (32, 3)
    """
    
    def __init__(self, 
                 input_size: int = 47,
                 hidden_size: int = 128,
                 num_layers: int = 2,
                 num_classes: int = 3,
                 dropout: float = 0.2):
        """
        Initialize LSTM classifier.
        
        Args:
            input_size: Number of input features
            hidden_size: Number of LSTM hidden units
            num_layers: Number of LSTM layers
            num_classes: Number of output classes
            dropout: Dropout probability
        """
        super(LSTMClassifier, self).__init__()
        
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.num_classes = num_classes
        
        # LSTM layers
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )
        
        # Fully connected layers
        self.fc1 = nn.Linear(hidden_size, 32)
        self.dropout1 = nn.Dropout(dropout)
        self.fc2 = nn.Linear(32, num_classes)
        
        # Activation
        self.relu = nn.ReLU()
        
        logger.info(f"Initialized LSTM: input={input_size}, hidden={hidden_size}, "
                   f"layers={num_layers}, classes={num_classes}")
    
    def forward(self, x):
        """
        Forward pass.
        
        Args:
            x: Input tensor with shape (batch, seq_len, input_size)
        
        Returns:
            Output tensor with shape (batch, num_classes)
        """
        # LSTM forward pass
        lstm_out, (h_n, c_n) = self.lstm(x)
        
        # Take the output from the last timestep
        last_output = lstm_out[:, -1, :]  # (batch, hidden_size)
        
        # Fully connected layers
        out = self.relu(self.fc1(last_output))
        out = self.dropout1(out)
        out = self.fc2(out)
        
        return out
    
    def predict_proba(self, x):
        """
        Predict class probabilities.
        
        Args:
            x: Input tensor
        
        Returns:
            Probabilities for each class
        """
        self.eval()
        with torch.no_grad():
            logits = self.forward(x)
            probas = torch.softmax(logits, dim=1)
        return probas


class LSTMTrainer:
    """
    Trainer for LSTM model with early stopping and checkpointing.
    
    Example:
        >>> model = LSTMClassifier()
        >>> trainer = LSTMTrainer(model)
        >>> history = trainer.train(train_loader, val_loader, epochs=50)
    """
    
    def __init__(self,
                 model: LSTMClassifier,
                 device: str = 'cpu',
                 learning_rate: float = 0.001,
                 class_weights: Optional[torch.Tensor] = None):
        """
        Initialize trainer.
        
        Args:
            model: LSTM model to train
            device: Device to use ('cpu' or 'cuda')
            learning_rate: Learning rate for optimizer
            class_weights: Weights for handling class imbalance
        """
        self.model = model.to(device)
        self.device = device
        
        # Loss function with class weights
        if class_weights is not None:
            class_weights = class_weights.to(device)
        self.criterion = nn.CrossEntropyLoss(weight=class_weights)
        
        # Optimizer
        self.optimizer = optim.Adam(model.parameters(), lr=learning_rate)
        
        # Learning rate scheduler
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, mode='min', factor=0.5, patience=5
        )
        
        # Training history
        self.history = {
            'train_loss': [],
            'train_acc': [],
            'val_loss': [],
            'val_acc': []
        }
        
        logger.info(f"Initialized trainer: device={device}, lr={learning_rate}")
    
    def train_epoch(self, train_loader: DataLoader) -> Tuple[float, float]:
        """
        Train for one epoch.
        
        Args:
            train_loader: Training data loader
        
        Returns:
            Average loss and accuracy for the epoch
        """
        self.model.train()
        total_loss = 0
        correct = 0
        total = 0
        
        for batch_idx, (data, target) in enumerate(train_loader):
            data, target = data.to(self.device), target.to(self.device)
            
            # Forward pass
            self.optimizer.zero_grad()
            output = self.model(data)
            loss = self.criterion(output, target)
            
            # Backward pass
            loss.backward()
            self.optimizer.step()
            
            # Statistics
            total_loss += loss.item()
            _, predicted = torch.max(output.data, 1)
            total += target.size(0)
            correct += (predicted == target).sum().item()
        
        avg_loss = total_loss / len(train_loader)
        accuracy = correct / total
        
        return avg_loss, accuracy
    
    def validate(self, val_loader: DataLoader) -> Tuple[float, float]:
        """
        Validate model.
        
        Args:
            val_loader: Validation data loader
        
        Returns:
            Average loss and accuracy
        """
        self.model.eval()
        total_loss = 0
        correct = 0
        total = 0
        
        with torch.no_grad():
            for data, target in val_loader:
                data, target = data.to(self.device), target.to(self.device)
                
                output = self.model(data)
                loss = self.criterion(output, target)
                
                total_loss += loss.item()
                _, predicted = torch.max(output.data, 1)
                total += target.size(0)
                correct += (predicted == target).sum().item()
        
        avg_loss = total_loss / len(val_loader)
        accuracy = correct / total
        
        return avg_loss, accuracy
    
    def train(self,
              train_loader: DataLoader,
              val_loader: Optional[DataLoader] = None,
              epochs: int = 50,
              early_stopping_patience: int = 10,
              save_path: Optional[str] = None) -> Dict:
        """
        Full training loop with early stopping.
        
        Args:
            train_loader: Training data loader
            val_loader: Validation data loader (optional)
            epochs: Maximum number of epochs
            early_stopping_patience: Patience for early stopping
            save_path: Path to save best model
        
        Returns:
            Training history dictionary
        """
        best_val_loss = float('inf')
        patience_counter = 0
        
        logger.info(f"Starting training for {epochs} epochs...")
        
        for epoch in range(epochs):
            # Train
            train_loss, train_acc = self.train_epoch(train_loader)
            self.history['train_loss'].append(train_loss)
            self.history['train_acc'].append(train_acc)
            
            # Validate
            if val_loader is not None:
                val_loss, val_acc = self.validate(val_loader)
                self.history['val_loss'].append(val_loss)
                self.history['val_acc'].append(val_acc)
                
                # Learning rate scheduling
                self.scheduler.step(val_loss)
                
                # Early stopping
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    patience_counter = 0
                    
                    # Save best model
                    if save_path:
                        self.save_model(save_path)
                        logger.info(f"Saved best model to {save_path}")
                else:
                    patience_counter += 1
                
                logger.info(f"Epoch {epoch+1}/{epochs}: "
                          f"Train Loss={train_loss:.4f}, Train Acc={train_acc:.4f}, "
                          f"Val Loss={val_loss:.4f}, Val Acc={val_acc:.4f}")
                
                # Check early stopping
                if patience_counter >= early_stopping_patience:
                    logger.info(f"Early stopping triggered at epoch {epoch+1}")
                    break
            else:
                logger.info(f"Epoch {epoch+1}/{epochs}: "
                          f"Train Loss={train_loss:.4f}, Train Acc={train_acc:.4f}")
        
        logger.info("Training complete!")
        return self.history
    
    def save_model(self, path: str):
        """Save model checkpoint."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'history': self.history
        }, path)
    
    def load_model(self, path: str):
        """Load model checkpoint."""
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.history = checkpoint['history']
        logger.info(f"Loaded model from {path}")


def calculate_class_weights(y_train: np.ndarray) -> torch.Tensor:
    """
    Calculate class weights for handling imbalance.
    
    Args:
        y_train: Training labels
    
    Returns:
        Tensor of class weights
    """
    from sklearn.utils.class_weight import compute_class_weight
    
    classes = np.unique(y_train)
    weights = compute_class_weight('balanced', classes=classes, y=y_train)
    
    logger.info(f"Class weights: {dict(zip(classes, weights))}")
    
    return torch.FloatTensor(weights)


def create_dataloaders(X_train: np.ndarray, y_train: np.ndarray,
                       X_val: Optional[np.ndarray] = None,
                       y_val: Optional[np.ndarray] = None,
                       batch_size: int = 16,
                       shuffle: bool = True) -> Dict[str, DataLoader]:
    """
    Create PyTorch data loaders from numpy arrays.
    
    Args:
        X_train: Training sequences
        y_train: Training labels
        X_val: Validation sequences (optional)
        y_val: Validation labels (optional)
        batch_size: Batch size
        shuffle: Whether to shuffle training data
    
    Returns:
        Dictionary with 'train_loader' and optionally 'val_loader'
    """
    # Convert to tensors
    X_train_tensor = torch.FloatTensor(X_train)
    y_train_tensor = torch.LongTensor(y_train)
    
    # Create datasets
    train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=shuffle)
    
    loaders = {'train_loader': train_loader}
    
    if X_val is not None and y_val is not None:
        X_val_tensor = torch.FloatTensor(X_val)
        y_val_tensor = torch.LongTensor(y_val)
        val_dataset = TensorDataset(X_val_tensor, y_val_tensor)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
        loaders['val_loader'] = val_loader
    
    return loaders
