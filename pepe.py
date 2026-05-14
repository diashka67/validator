import pandas as pd
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Type
import re

class ClientTypeEnum(Enum):
    LEGAL = "юр. лицо"
    PHYSICAL = "физ. лицо"

class OperationTypeEnum(Enum):
    WITHDRAWAL = "списание средств"
    DEPOSIT = "получение средств"

class PaymentTypeEnum(Enum):
    CASH = "наличный"
    CASHLESS = "безналичный"

class CityEnum(Enum):
    VITEBSK = "Витебск"
    MOGILEV = "Могилев"
    GRODNO = "Гродно"
    BREST = "Брест"
    GOMEL = "Гомель"
    MINSK = "Минск"

class StatusEnum(Enum):
    SUCCESS = "успешно"
    WRONG_PIN = "неправильный ввод пин-кода"
    INSUFFICIENT_FUNDS = "недостаточно средств"

class CommissionFlagEnum(Enum):
    YES = "да"
    NO = "нет"

class AbstractOperationValidator(ABC):
    @abstractmethod
    def validate(self, df: pd.DataFrame, **kwargs: Any) -> bool:
        """Выполняет валидацию DataFrame. Возвращает True при успехе."""
        pass

class EmptyValidator(AbstractOperationValidator):
    def validate(self, df: pd.DataFrame, **kwargs: Any) -> bool:
        if df.empty:
            raise pd.errors.EmptyDataError("Файл пуст")
        return True

class EnumColumnValidator(AbstractOperationValidator):
    """Проверяет, что все значения колонки принадлежат заданному Enum"""
    def validate(self, df: pd.DataFrame, column: str, enum_class: Type[Enum], **kwargs: Any) -> bool:
        if column not in df.columns:
            raise ValueError(f"Столбец '{column}' отсутствует в DataFrame")
            
        allowed = {e.value for e in enum_class}
        actual = set(df[column].dropna().unique())
        invalid = actual - allowed
        if invalid:
            raise ValueError(f"Столбец '{column}' содержит недопустимые значения: {invalid}")
        return True

class PatternColumnValidator(AbstractOperationValidator):
    """Проверяет колонку по регулярному выражению (дата, время, банк)"""
    def validate(self, df: pd.DataFrame, column: str, pattern: str, **kwargs: Any) -> bool:
        regex = re.compile(pattern)
        invalid_mask = df[column].astype(str).apply(lambda x: not bool(regex.fullmatch(x)))
        if invalid_mask.any():
            bad = df[invalid_mask][column].head(3).tolist()
            raise ValueError(f"Столбец '{column}' нарушает формат '{pattern}'. Примеры: {bad}")
        return True

class NumericNonNegativeValidator(AbstractOperationValidator):
    """Проверяет, что колонка числовая и ≥ 0"""
    def validate(self, df: pd.DataFrame, column: str, **kwargs: Any) -> bool:
        df[column] = pd.to_numeric(df[column], errors='coerce')
        if df[column].isna().any():
            raise ValueError(f"Столбец '{column}' содержит нечисловые значения")
        if (df[column] < 0).any():
            raise ValueError(f"Столбец '{column}' содержит отрицательные значения")
        return True

class Check:
    def __init__(self):
        self.df: pd.DataFrame | None = None

        self._validators: Dict[str, AbstractOperationValidator] = {
            "empty": EmptyValidator(),
            "enum_col": EnumColumnValidator(),
            "pattern_col": PatternColumnValidator(),
            "numeric_col": NumericNonNegativeValidator()
        }

    def open_file(self):
        try:
            name_file = input('введите имя файла: ')
            if name_file != 'var5.csv':
                raise ValueError('ПЕРЕСМОТРИ НАЗВАНИЕ ФАЙЛА!!!')
            
            col_names = [
                'client_type', 'operation_type', 'amount', 'payment_type', 'city',
                'bank', 'date', 'time', 'status', 'commission_flag', 'commission_amount'
            ]
            self.df = pd.read_csv(name_file, names=col_names)
            print(' Файл успешно открыт и структурирован')
            
        except (FileNotFoundError, ValueError) as e:
            print(f' {e}')
        except pd.errors.ParserError:
            print(" Файл поврежден или имеет неверный формат")
        except Exception as e:
            print(f' Не удалось открыть файл: {e}')

    def _run(self, validator_key: str, **kwargs) -> bool:
        if self.df is None:
            print(' Файл не был открыт')
            return False
            
        validator = self._validators.get(validator_key)
        if not validator:
            print(f' Валидатор "{validator_key}" не зарегистрирован')
            return False

        try:
            validator.validate(self.df, **kwargs)
            print(f' Проверка "{validator_key}" пройдена')
            return True
        except Exception as e:
            print(f' Ошибка "{validator_key}": {e}')
            return False

    # --- Обертки для каждой колонки ---
    def validate_client_type(self) -> bool:
        return self._run("enum_col", column='client_type', enum_class=ClientTypeEnum)

    def validate_operation_type(self) -> bool:
        return self._run("enum_col", column='operation_type', enum_class=OperationTypeEnum)

    def validate_payment_type(self) -> bool:
        return self._run("enum_col", column='payment_type', enum_class=PaymentTypeEnum)

    def validate_city(self) -> bool:
        return self._run("enum_col", column='city', enum_class=CityEnum)

    def validate_status(self) -> bool:
        return self._run("enum_col", column='status', enum_class=StatusEnum)

    def validate_commission_flag(self) -> bool:
        return self._run("enum_col", column='commission_flag', enum_class=CommissionFlagEnum)

    def validate_bank(self) -> bool:
        # Формат: НазваниеБанка-КОД-НОМЕР
        return self._run("pattern_col", column='bank', pattern=r'^[А-Яа-яЁё]+-[A-Z]{4}-\d{3}$')

    def validate_date(self) -> bool:
        return self._run("pattern_col", column='date', pattern=r'^\d{2}-\d{2}-\d{4}$')

    def validate_time(self) -> bool:
        return self._run("pattern_col", column='time', pattern=r'^\d{2}:\d{2}:\d{2}$')

    def validate_amount(self) -> bool:
        return self._run("numeric_col", column='amount')

    def validate_commission_amount(self) -> bool:
        return self._run("numeric_col", column='commission_amount')

    def validate_all(self) -> bool:
        """Запускает валидацию всех колонок последовательно"""
        methods = [
            self.validate_client_type, self.validate_operation_type,
            self.validate_payment_type, self.validate_city,
            self.validate_status, self.validate_commission_flag,
            self.validate_bank, self.validate_date, self.validate_time,
            self.validate_amount, self.validate_commission_amount
        ]
        print("\n Запуск полной валидации всех колонок...")
        return all(m() for m in methods)
