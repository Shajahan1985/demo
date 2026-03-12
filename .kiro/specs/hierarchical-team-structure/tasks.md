# Implementation Plan: Hierarchical Team Structure

## Overview

This implementation plan transforms the Asset Tracking System's flat team structure into a two-level hierarchical model with parent teams and sub-teams. The approach follows Django best practices, maintains backward compatibility with existing asset assignments, and includes comprehensive validation to prevent circular references and maintain data integrity.

## Tasks

- [x] 1. Update Team model with hierarchical support
  - [x] 1.1 Add parent field and hierarchy methods to Team model
    - Add self-referential ForeignKey parent field with CASCADE delete
    - Implement clean() method with validation for circular references, self-reference, depth limits, and parent team constraints
    - Add is_parent, hierarchy_level, get_all_sub_teams(), and get_hierarchy_display() methods
    - Add database indexes for parent field and composite (parent, name) index
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 9.1, 9.2, 9.3, 9.4, 9.5_

  - [x] 1.2 Write property test for circular reference prevention
    - **Property 1: Circular Reference Prevention**
    - **Validates: Requirements 1.4, 4.5, 9.1, 9.2, 9.3, 10.6**

  - [x] 1.3 Write property test for hierarchy depth limitation
    - **Property 2: Hierarchy Depth Limitation**
    - **Validates: Requirements 9.4**

  - [x] 1.4 Write property test for parent team constraint
    - **Property 3: Parent Team Constraint**
    - **Validates: Requirements 9.5**

  - [x] 1.5 Write property test for team classification
    - **Property 4: Team Classification by Hierarchy Level**
    - **Validates: Requirements 1.2, 1.3**

  - [x] 1.6 Write property test for multiple sub-teams support
    - **Property 5: Multiple Sub-Teams Support**
    - **Validates: Requirements 1.6**

  - [x] 1.7 Write unit tests for Team model validation
    - Test specific examples: self-reference, 3-level hierarchy, parent with children becoming sub-team
    - Test edge cases: empty names, special characters, very long names
    - _Requirements: 1.4, 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 2. Create custom Team manager for efficient queries
  - [x] 2.1 Implement TeamManager with hierarchy query methods
    - Add get_hierarchy() method using select_related and prefetch_related
    - Add get_parent_teams() method filtering by parent__isnull=True
    - Add get_sub_teams() method filtering by parent__isnull=False
    - Add get_hierarchical_choices() method returning formatted choices for dropdowns
    - Attach manager to Team model
    - _Requirements: 2.1, 2.2, 2.5, 2.6, 8.1, 8.2, 8.3, 8.4_

  - [x] 2.2 Write property test for hierarchical dropdown ordering
    - **Property 8: Hierarchical Dropdown Ordering**
    - **Validates: Requirements 2.1, 2.5, 2.6**

  - [x] 2.3 Write property test for team queryset filtering
    - **Property 21: Team Queryset Filtering**
    - **Validates: Requirements 4.7**

  - [x] 2.4 Write unit tests for TeamManager methods
    - Test get_hierarchical_choices() returns correct format and ordering
    - Test query efficiency with assertNumQueries
    - _Requirements: 2.1, 2.5, 2.6, 8.4_

- [x] 3. Create database migrations
  - [x] 3.1 Create schema migration for parent field
    - Generate migration adding parent ForeignKey field to Team model
    - Add database index on parent field
    - Add composite index on (parent, name)
    - Ensure field is nullable and blank for backward compatibility
    - _Requirements: 1.1, 8.1_

  - [x] 3.2 Create data migration for pre-populated teams
    - Create parent teams: Marketing, Developers, Data Center Team, Accounts Team, Iboss Support Team
    - Create Not Applicable team
    - Create 19 sub-teams under Developers with specified names
    - Use get_or_create to handle existing teams (idempotency)
    - Implement reverse migration to clear parent relationships
    - Wrap operations in transaction for rollback on error
    - Add logging for all team creation operations
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 7.1, 7.2, 7.3, 7.4, 7.5_

  - [x] 3.3 Write property test for migration data preservation
    - **Property 16: Migration Data Preservation**
    - **Validates: Requirements 3.8, 5.3, 7.6**

  - [x] 3.4 Write property test for migration idempotency
    - **Property 17: Migration Idempotency**
    - **Validates: Requirements 3.9**

  - [x] 3.5 Write unit tests for migrations
    - Test forward migration creates parent field with correct constraints
    - Test data migration creates all specified teams
    - Test reverse migration removes parent field and preserves team names
    - Test migration handles existing teams with matching names
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 7.5, 7.6_

- [x] 4. Checkpoint - Run migrations and verify database state
  - Run migrations in development environment
  - Verify all parent teams and sub-teams are created
  - Verify existing asset-team assignments are preserved
  - Ensure all tests pass, ask the user if questions arise

- [x] 5. Create hierarchical team form field
  - [x] 5.1 Implement HierarchicalTeamChoiceField
    - Create custom ModelChoiceField subclass
    - Override label_from_instance() to add indentation for sub-teams
    - Use Team.objects.get_hierarchy() for queryset
    - _Requirements: 2.2, 2.7_

  - [x] 5.2 Update AssetForm to use hierarchical team field
    - Replace team field with HierarchicalTeamChoiceField
    - Ensure field accepts both parent teams and sub-teams
    - Add appropriate widget styling
    - _Requirements: 2.3, 5.2, 6.1_

  - [x] 5.3 Write property test for sub-team display indentation
    - **Property 9: Sub-Team Display Indentation**
    - **Validates: Requirements 2.2, 2.7**

  - [x] 5.4 Write property test for team selection flexibility
    - **Property 10: Both Parent and Sub-Team Selection Allowed**
    - **Validates: Requirements 2.3**

  - [x] 5.5 Write unit tests for form field
    - Test label_from_instance() returns correct indentation
    - Test form validation accepts both parent and sub-teams
    - Test form validation rejects invalid team IDs
    - _Requirements: 2.2, 2.3, 2.7, 6.2_

- [x] 6. Update Django admin interface
  - [x] 6.1 Enhance TeamAdmin with hierarchy display
    - Add get_hierarchy_display() method to list_display
    - Add sub_team_count() method to show number of sub-teams
    - Add parent field to fieldsets
    - Add list_filter for parent field
    - Add search_fields for name and parent__name
    - Override get_queryset() to use select_related and prefetch_related
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.6, 4.7, 9.6_

  - [x] 6.2 Write unit tests for admin interface
    - Test admin displays hierarchy correctly
    - Test admin allows creating teams with and without parents
    - Test admin validation prevents circular references
    - Test admin filtering by parent teams and sub-teams
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.7, 9.6_

- [x] 7. Implement Team API serializer and views
  - [x] 7.1 Create TeamSerializer with hierarchy information
    - Add parent_id and parent_name read-only fields
    - Add sub_teams SerializerMethodField returning list of sub-team IDs and names
    - Add is_parent and hierarchy_level read-only fields
    - Implement validate_parent() method with circular reference and depth checks
    - _Requirements: 10.1, 10.2, 10.5, 10.6, 10.7_

  - [x] 7.2 Create API endpoints for team hierarchy
    - Implement list endpoint returning all teams with hierarchy info
    - Implement retrieve endpoint for single team with parent/children
    - Implement create endpoint accepting parent team identifier
    - Implement update endpoint with hierarchy validation
    - Implement delete endpoint with cascade behavior
    - Add endpoint to retrieve sub-teams for a specific parent team
    - _Requirements: 10.3, 10.4, 10.5, 10.6, 10.7_

  - [x] 7.3 Write property test for API sub-team serialization
    - **Property 22: API Sub-Team Serialization**
    - **Validates: Requirements 10.1**

  - [x] 7.4 Write property test for API parent team serialization
    - **Property 23: API Parent Team Serialization**
    - **Validates: Requirements 10.2**

  - [x] 7.5 Write property test for API validation error responses
    - **Property 25: API Validation Error Responses**
    - **Validates: Requirements 10.7**

  - [x] 7.6 Write unit tests for API endpoints
    - Test POST /api/teams/ creates team with parent
    - Test PUT /api/teams/{id}/ updates parent assignment
    - Test PUT with circular reference returns 400
    - Test DELETE /api/teams/{id}/ cascades to sub-teams
    - Test GET /api/teams/{id}/sub-teams/ returns correct sub-teams
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7_

- [x] 8. Update asset views and templates
  - [x] 8.1 Update asset detail view to show team hierarchy
    - Modify template to display team with hierarchy context for sub-teams
    - Display "Not Applicable" for Not Applicable team
    - _Requirements: 5.4, 6.3, 6.4_

  - [x] 8.2 Update asset list view with team filtering
    - Add filtering by both parent teams and sub-teams
    - Update queryset to use select_related for team and team__parent
    - _Requirements: 6.5, 8.4_

  - [x] 8.3 Implement team statistics aggregation
    - Create view or method to aggregate asset statistics by team
    - For parent teams, include assets from all sub-teams
    - _Requirements: 6.6_

  - [x] 8.4 Write property test for asset team assignment
    - **Property 11: Asset Team Assignment Flexibility**
    - **Validates: Requirements 5.2, 5.5**

  - [x] 8.5 Write property test for asset team display
    - **Property 12: Asset Team Display**
    - **Validates: Requirements 5.4, 6.3**

  - [x] 8.6 Write property test for team filter inclusivity
    - **Property 13: Team Filter Inclusivity**
    - **Validates: Requirements 6.5**

  - [x] 8.7 Write property test for parent team statistics aggregation
    - **Property 14: Parent Team Statistics Aggregation**
    - **Validates: Requirements 6.6**

  - [x] 8.8 Write unit tests for asset views
    - Test asset detail shows correct team hierarchy display
    - Test asset list filtering by parent and sub-teams
    - Test statistics aggregation includes sub-team assets
    - _Requirements: 5.4, 6.3, 6.4, 6.5, 6.6_

- [x] 9. Implement cascade deletion and cache management
  - [x] 9.1 Verify cascade deletion behavior
    - Ensure parent deletion cascades to sub-teams (CASCADE on parent FK)
    - Ensure team deletion sets asset team to null (SET_NULL on asset FK)
    - Add admin confirmation dialog showing affected sub-teams before deletion
    - _Requirements: 1.7, 5.6_

  - [x] 9.2 Implement cache invalidation for team hierarchy
    - Add cache invalidation on team save/delete
    - Cache team hierarchy structure where appropriate
    - _Requirements: 8.5, 8.6_

  - [x] 9.3 Write property test for parent deletion cascade
    - **Property 6: Parent Deletion Cascades to Sub-Teams**
    - **Validates: Requirements 1.7**

  - [x] 9.4 Write property test for team deletion asset handling
    - **Property 7: Team Deletion Sets Asset Team to Null**
    - **Validates: Requirements 5.6**

  - [x] 9.5 Write property test for cache invalidation
    - **Property 20: Cache Invalidation on Hierarchy Change**
    - **Validates: Requirements 8.6**

  - [x] 9.6 Write unit tests for deletion and caching
    - Test deleting parent team deletes all sub-teams
    - Test deleting team with assets sets asset.team to None
    - Test cache is invalidated when team hierarchy changes
    - _Requirements: 1.7, 5.6, 8.5, 8.6_

- [x] 10. Final checkpoint - Integration testing and verification
  - Run complete test suite (property tests and unit tests)
  - Verify all 25 correctness properties pass
  - Test complete workflow: create parent → create sub-teams → assign to assets → filter → aggregate statistics
  - Verify admin interface displays hierarchy correctly
  - Test API endpoints with various hierarchy scenarios
  - Verify migration rollback works correctly
  - Ensure all tests pass, ask the user if questions arise

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples, edge cases, and integration points
- Checkpoints ensure incremental validation at key milestones
- The implementation uses Django's built-in features (ForeignKey CASCADE, model validation, admin customization)
- All database operations are wrapped in transactions for data safety
- Query optimization uses select_related and prefetch_related to minimize database hits
