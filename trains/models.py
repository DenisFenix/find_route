from django.core.exceptions import ValidationError
from django.db import models

from cities.models import City


class Train(models.Model):
    name = models.CharField(max_length=50, unique=True,
                            verbose_name='Номер поезда')
    travel_time = models.PositiveSmallIntegerField(verbose_name='Время в пути')
    from_city = models.ForeignKey(City, on_delete=models.CASCADE,
                                  # null=True, blank=True
                                  related_name='from_city_set',
                                  verbose_name='Из какого города'
                                  )
    # models.CASCADE() - при удалении записи города, удаляются все привязанные к городу записи
    # models.PROTECT() - защита от удаления: записи не удалятся до тех пор, пока они привязаны в других таблицах
    # SET_NULL() - при удалении записи в таблице City внутри данной записи мы выставляем значение NULL, при этом
    # необходимо, чтобы данная запись была установлена в это значение null=True
    to_city = models.ForeignKey('cities.City', on_delete=models.CASCADE,
                                related_name='to_city_set',
                                verbose_name='В какой город'
                                )

    def __str__(self):
        return f'Поезд №{self.name} из города {self.from_city}'

    class Meta:
        verbose_name = 'Поезд'
        verbose_name_plural = 'Поезда'
        # Метод сортировки на странице
        # name - по имени, travel_time - по времени, from_city - из какого города, to_city - в какой город
        ordering = ['travel_time']

    def clean(self):
        if self.from_city == self.to_city:
            raise ValidationError('Измените город прибытия')
        qs = Train.objects.filter(
            from_city=self.from_city, to_city=self.to_city,
            travel_time=self.travel_time).exclude(pk=self.pk)
        # Train == self.__class__
        if qs.exists():
            raise ValidationError('Измените время в пути')

    # Есть несколько методов QuerySet, которые сохраняют записи в БД, но при этом метод,
    # который прописан в классе models, он  не вызывается.
    # Перед созданием новой записи ее нужно сохранять через метод save(),
    # потому что применение методов QuerySet не всегда вызывает вызов метода set у Python
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
