# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
import random
from django.db.models import Count
from django.contrib.auth.models import User

from skills.models import StudentSkill


class AuthUserManager(models.Manager):
    def get_queryset(self):
        return super(AuthUserManager, self).get_queryset().select_related('user')


class Professor(models.Model):

    objects = AuthUserManager()
    user = models.OneToOneField(User)
    is_pending = models.BooleanField(default=True)
    code = models.BigIntegerField(null=True, blank=True)
    criterias = models.ManyToManyField('skills.Criteria', related_name="ordering_criteria+")

    def __unicode__(self):
        return ("%s %s" % (
        self.user.first_name, self.user.last_name)) if self.user.first_name or self.user.last_name else self.user.username

    def assign_targets(self, student, target_skills):
        """ Assign target skills to the student

            Set the is_target flag on matching student skills.
            If there is none, then a student skill is created for the target and for each prerequisite skill.
        """
        student_skills = StudentSkill.objects.filter(student=student)
        for target_skill in target_skills:
            found = False
            for student_skill in student_skills:
                if student_skill.skill == target_skill:
                    student_skill.is_target = True
                    student_skill.save()
                    found = True
                    break
            if not found:
                StudentSkill.objects.create(
                    student=student,
                    skill=target_skill,
                    is_target=True
                )
                for prerequisite in target_skill.skill.get_prerequisites_skills():
                    if prerequisite not in student_skills:
                        StudentSkill.objects.create(
                            student=student,
                            skill=prerequisite,
                        )

    class Meta:
        ordering = ['user__last_name', 'user__first_name']


class Student(models.Model):

    objects = AuthUserManager()

    user = models.OneToOneField(User)
    is_pending = models.BooleanField(default=True)
    code = models.IntegerField(null=True, blank=True)
    code_created_at = models.DateTimeField(auto_now=True)
    #learning_track = models.ManyToManyField('skills.StudentSkill', through="skills.LearningTrack")

    def __unicode__(self):
        return ("%s %s" % (
        self.user.first_name, self.user.last_name)) if self.user.first_name or self.user.last_name else self.user.username


    def generate_new_code(self):
        """Generate studenty password"""
        new_code = "%s" % (random.randint(1000, 9999))
        self.code = new_code
        self.is_pending = True
        self.save()
        return new_code

    class Meta:
        ordering = ['user__last_name']

    def get_email(self):
        if self.user.email.endswith("@example.com"):
            return ""
        return self.user.email

    def done_tests(self):
        return self.teststudent_set.filter(finished_at__isnull=False)

    def todo_tests(self):
        return self.teststudent_set.filter(finished_at__isnull=True)

    def get_last_test(self):
        return self.teststudent_set.order_by('-test__created_at').first()

    def has_recommended_skills(self):
        for student_skill in self.studentskill_set.all():
            if student_skill.recommended_to_learn():
                return True

        return False
